#
# This file is protected by Copyright. Please refer to the COPYRIGHT file
# distributed with this source distribution.
#
# This file is part of REDHAWK rest-python.
#
# REDHAWK rest-python is free software: you can redistribute it and/or modify it under
# the terms of the GNU Lesser General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option) any
# later version.
#
# REDHAWK rest-python is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License for more
# details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see http://www.gnu.org/licenses/.
#
# system imports
import logging

from bulkio.bulkioInterfaces import BULKIO__POA
from bulkio import sri
from ossie.properties import props_to_dict
from omniORB import CORBA

# third party imports
from tornado import ioloop, gen
from tornado import websocket

import time
import json
import bulkio_limiter

from model.domain import Domain, ResourceNotFound
from asyncport import AsyncPort

from crossdomainsocket import CrossDomainSockets

def enum(**enums):
    return type('Enum', (), enums)

# Control messages are a dictionary of type and value.  The type should be
# one of these enumerations.
# E.g.:     ControlMessage = { 'type': 0, 'value': 1024 }
ControlEnum = enum(xMax=0, xBegin=1, xEnd=2, xZoomIn=3, xZoomReset=4, yMax=5, yBegin=6, yEnd=7, yZoomIn=8, yZoomReset=9, MaxPPS=10)


class BulkIOWebsocketHandler(CrossDomainSockets):
    def initialize(self, kind, redhawk=None, _ioloop=None):
        self.kind = kind
        self.redhawk = redhawk
        if not _ioloop:
            _ioloop = ioloop.IOLoop.current()
        self._ioloop = _ioloop

        # For on-the-fly per-client down-sampling
        # Current options: 0=NoLimit, else=Limit
        self._xMax = 1024
        self._yMax = 1024

        # The ACTIVE on-the-fly per-client zooming parameters
        # These are set from the STAGED values from a xZoomIn/yZoomIn command
        self._xBegin = None
        self._xEnd = None
        self._yBegin = None
        self._yEnd = None

        # The STAGED on-the-fly per-client zooming parameters
        # These are set by commands from UI
        self._xBeginStaged = None
        self._xEndStaged = None
        self._yBeginStaged = None
        self._yEndStaged = None

        # The down-sampling ratios calculated from the last call to the bulio_limiter
        self._xFactor = 1
        self._yFactor = 1

        # Map of SRIs seen on this port.
        self._SRIs = dict()

    @gen.coroutine
    def open(self, *args):
        try:
            logging.debug("BulkIOWebsocketHandler open kind=%s, path=%s", self.kind, args)
            obj, path = yield self.redhawk.get_object_by_path(args, path_type=self.kind)
            logging.debug("Found object %s", dir(obj))

            for p in obj.ports:
                if p.name == path[0]:
                    if p._direction == 'Uses':
                        namespace = p._using.nameSpace

                        if namespace == 'BULKIO':
                            self.port = p
                            logging.debug("Found port %s", self.port)

                            data_type = p._using.name
                            bulkio_poa = getattr(BULKIO__POA, data_type)
                            logging.debug(bulkio_poa)

                            self.async_port = AsyncPort(bulkio_poa, self._pushSRI, self._pushPacket)

                            if len(path) == 3:
                                self._connectionId = path[2][1:]
                            else:
                                self._connectionId = 'rest-python-%s' % id(self)

                            self.port.ref.connectPort(self.async_port.getPort(), self._connectionId)
                            logging.info("Opened websocket to %s, %s", self.port, self._connectionId)

                            break
                        else:
                            raise ValueError("Port '%s' is not a BULKIO port" % path[0])
                    else:
                        raise ValueError("Port '%s' is not a uses" % path[0])
            else:
                raise ValueError("Could not find port of name '%s'" % path[0])

        except ResourceNotFound, e:
            self.write_message(dict(error='ResourceNotFound', message=str(e)))
            self.close()
        except Exception, e:
            logging.exception('Error with request %s' % self.request.full_url())
            self.write_message(dict(error='SystemError', message=str(e)))
            self.close()

    def on_message(self, message):
        try:
            # Parse a JSON string into a dictionary
            ctrl = json.loads(message)

            # Convert the value to integer
            ctrlValueInt = int(ctrl['value'])

            # Set the maximum number of samples --------------------------------
            if (ctrl['type'] == ControlEnum.xMax):
                if (ctrlValueInt > 0):
                    self._xMax = ctrlValueInt
                    logging.info('Bulkio packet size limited to {0} samples on the X axis'.format(ctrlValueInt))
                else:
                    self._xMax = None
                    logging.info('Bulkio packet size limit removed from the X axis')

            # Set the STAGED zoom region ---------------------------------------
            elif (ctrl['type'] == ControlEnum.xBegin):
                # Calculate the index based on the original packet size since we
                # slice and then downsample in the bulkio_limiter
                self._xBeginStaged = ctrlValueInt * self._xFactor
                # If there is already a start index, this means that we are
                # zooming on a zoomed region and we need to adjust the indices
                # to reflect the previously zoomed region.
                if (self._xBegin):
                    self._xBeginStaged += self._xBegin
                # Log the indices
                logging.info('Bulkio packet zoom begin index set to {0} on the X axis'.format(self._xBeginStaged))
            elif (ctrl['type'] == ControlEnum.xEnd):
                # Calculate the index based on the original packet size since we
                # slice and then downsample in the bulkio_limiter
                self._xEndStaged = ctrlValueInt * self._xFactor
                # If there is already a start index, this means that we are
                # zooming on a zoomed region and we need to adjust the indices
                # to reflect the previously zoomed region.
                if (self._xBegin):
                    self._xEndStaged += self._xBegin
                # Log the indices
                logging.info('Bulkio packet zoom end index set to {0} on the X axis'.format(self._xEndStaged))

            # Zoom commands ----------------------------------------------------
            elif (ctrl['type'] == ControlEnum.xZoomIn):
                # Make the staged values ACTIVE
                self._xBegin = self._xBeginStaged
                self._xEnd = self._xEndStaged
                self._xBeginStaged = None
                self._xEndStaged = None
                logging.info('Zoom IN commanded for the X axis with indices: ['+str(self._xBegin)+','+str(self._xEnd)+']')
            elif (ctrl['type'] == ControlEnum.xZoomReset):
                self._xBegin = None
                self._xEnd = None
                self._xBeginStaged = None
                self._xEndStaged = None
                logging.info('Zoom RESET commanded for the X axis')

            # Set the maximum number of samples --------------------------------
            elif (ctrl['type'] == ControlEnum.yMax):
                if (ctrlValueInt > 0):
                    self._yMax = ctrlValueInt
                    logging.info('Bulkio packet size limited to {0} samples on the Y axis'.format(ctrlValueInt))
                else:
                    self._yMax = None
                    logging.info('Bulkio packet size limit removed from the Y axis')

            # Set the STAGED zoom region ---------------------------------------
            elif (ctrl['type'] == ControlEnum.yBegin):
                # Calculate the index based on the original packet size since we
                # slice and then downsample in the bulkio_limiter
                self._yBeginStaged = ctrlValueInt * self._yFactor
                # If there is already a start index, this means that we are
                # zooming on a zoomed region and we need to adjust the indices
                # to reflect the previously zoomed region.
                if (self._yBegin):
                    self._yBeginStaged += self._yBegin
                # Log the indices
                logging.info('Bulkio packet zoom begin index set to {0} on the Y axis'.format(self._yBeginStaged))
            elif (ctrl['type'] == ControlEnum.yEnd):
                # Calculate the index based on the original packet size since we
                # slice and then downsample in the bulkio_limiter
                self._yEndStaged = ctrlValueInt * self._yFactor
                # If there is already a start index, this means that we are
                # zooming on a zoomed region and we need to adjust the indices
                # to reflect the previously zoomed region.
                if (self._yBegin):
                    self._yEndStaged += self._yBegin
                # Log the indices
                logging.info('Bulkio packet zoom end index set to {0} on the Y axis'.format(self._yEndStaged))

            # Zoom commands ----------------------------------------------------
            elif (ctrl['type'] == ControlEnum.yZoomIn):
                # Make the staged values ACTIVE
                self._yBegin = self._yBeginStaged
                self._yEnd = self._yEndStaged
                self._yBeginStaged = None
                self._yEndStaged = None
                logging.info('Zoom IN commanded for the Y axis with indices: ['+str(self._yBegin)+','+str(self._yEnd)+']')
            elif (ctrl['type'] == ControlEnum.yZoomReset):
                self._yBegin = None
                self._yEnd = None
                self._yBeginStaged = None
                self._yEndStaged = None
                logging.info('Zoom RESET commanded for the Y axis')

            # Set the max PPS --------------------------------------------------
            elif (ctrl['type'] == ControlEnum.MaxPPS):
                logging.warning('Packets per second (PPS) not implemented yet.')

        except Exception as e:
            self.write_message(dict(error='SystemError', message=str(e)))

    def on_close(self):
        logging.debug('Stream CLOSE')
        try:
            self.port.ref.disconnectPort(self._connectionId)
            logging.info("Closed websocket to %s, %s", self.port, self._connectionId)
        except CORBA.TRANSIENT:
            pass
        except Exception, e:
            logging.exception('Error disconnecting port %s' % self._connectionId)

    def _pushSRI(self, newSRI):
        origSRI, changed = self._getSRI(newSRI.streamID)
        if origSRI is not None:
            changed = sri.compare(origSRI, newSRI)
        self._SRIs[newSRI.streamID] = (newSRI, changed)

    def _getSRI(self, streamID):
        return self._SRIs.get(streamID, (None, True))

    def _pushPacket(self, data, ts, EOS, stream_id):
        # Retrieve SRI from stream_id
        sri, sriChangedFromPacket = self._getSRI(stream_id)

        # Check if any limiting parameter exists
        if (self._hasLimitingParameter()):
            # Call the limit function (the "True" flags tell the function to use the mean() down-sampling)
            outData, outSRI, self._xFactor, self._yFactor, sriChangedFromLimiter, warningMessage = bulkio_limiter.limit(
                data, sri, self._xMax, self._xBegin, self._xEnd, True, self._yMax, self._yBegin, self._yEnd, True
            )

            # Logging for debug (comment out operationally)
            #logging.info("connection_id: " + str(self._connectionId))
            #logging.info("bulkio_limiter info: \n" +
            #             "    originalWordLength="+str(len(data))+", finalWordLength="+str(len(outData))+", originalSubsize="+str(sri.subsize)+", finalSubsize="+str(outSRI.subsize)+"\n"+
            #             "    xMax="+str(self._xMax)+", xBegin="+str(self._xBegin)+", xEnd="+str(self._xEnd)+", xDownSampFactor="+str(self._xFactor)+"\n"+
            #             "    yMax="+str(self._yMax)+", yBegin="+str(self._yBegin)+", yEnd="+str(self._yEnd)+", yDownSampFactor="+str(self._yFactor)+"\n"+
            #             "    sriChangedFromLimiter="+str(sriChangedFromLimiter))

            # Print warnings if they exist
            if (warningMessage):
                logging.warning('bulkio_limiter.limit(): ' + warningMessage)
        else:
            # Don't do anything if no limiting parameter exists
            outData = data
            outSRI = bulkio_limiter.copy_sri(sri)
            sriChangedFromLimiter = False

        # Tack on SRI, Package, Deliver.
        outSRI.keywords = props_to_dict(outSRI.keywords)
        packet = dict(
            streamID   = stream_id,
            T          = ts.__dict__,
            EOS        = EOS,
            sriChanged = (sriChangedFromPacket or sriChangedFromLimiter),
            SRI        = outSRI.__dict__,
            type       = self.port._using.name,
            dataBuffer = outData
            )
        self._ioloop.add_callback(self.write_message, packet)

    def _hasLimitingParameter(self):
        # Check if any of the X axis parameters are not None
        if (self._xMax or self._xBegin or self._xEnd):
            return True
        # Check if any of the Y axis parameters are not None
        if (self._yMax or self._yBegin or self._yEnd):
            return True
        # Return false if all the parameters are None
        return False

    def write_message(self, *args, **ioargs):
        # hide WebSocketClosedError because it's very likely
        try:
            super(BulkIOWebsocketHandler, self).write_message(*args, **ioargs)
        except websocket.WebSocketClosedError:
            logging.debug('Received WebSocketClosedError. Ignoring')
            self.close()
