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

import json
import numpy

from model.domain import Domain, ResourceNotFound
from asyncport import AsyncPort

from crossdomainsocket import CrossDomainSockets

def enum(**enums):
    return type('Enum', (), enums)

# Control messages are a dictionary of type and value.  The type should be
# one of these enumerations.
# E.g.:     ControlMessage = { 'type': 0, 'value': 1024 }
ControlEnum = enum(MaxWidth=0, MaxPPS=1)


class BulkIOWebsocketHandler(CrossDomainSockets):
    def initialize(self, kind, redhawk=None, _ioloop=None):
        self.kind = kind
        self.redhawk = redhawk
        if not _ioloop:
            _ioloop = ioloop.IOLoop.current()
        self._ioloop = _ioloop

        # For on-the-fly per-client decimation
        self._outputWidth = None

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
            ctrl = json.loads(message)

            if (ctrl['type'] == ControlEnum.MaxWidth):
                if 0 < ctrl['value']:
                    self._outputWidth = ctrl['value']
                    logging.info('Decimation requested to {0} samples'.format(ctrl['value']))
                else:
                    self._outputWidth = None
                    logging.info('Decimation disabled')

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
            changed = sri.compareSRI(origSRI, newSRI)
        self._SRIs[newSRI.streamID] = (newSRI, changed)

    def _getSRI(self, streamID):
        return self._SRIs.get(streamID, (None, True))

    def _pushPacket(self, data, ts, EOS, stream_id):
        data = numpy.array(data)

        if None == self._outputWidth:
            self._outputWidth = data.size 

        # Get SRI and modify if necessary (from decimation)
        SRI, changed = self._getSRI(stream_id)
        outSRI = copy_sri(SRI)
        if 0 < data.size and data.size != self._outputWidth:
            D, M = divmod(data.size, self._outputWidth)
            if 0 == M and 1 < D:
                # Mean decimate
                data = data.reshape(-1, D).mean(axis=1)
                outSRI.xdelta = SRI.xdelta * D
                changed = True
            else:
                # Restore...invalid setting.
                # TODO: Support interp+decimate rather than just
                #       neighbor-mean
                logging.warning('Interpolate+decimate not supported.  Restoring original output width.')
                self._outputWidth = None

        # Tack on SRI, Package, Deliver.
        outSRI.keywords = props_to_dict(outSRI.keywords)
        packet = dict(
            streamID   = stream_id,
            T          = ts.__dict__,
            EOS        = EOS,
            sriChanged = changed,
            SRI        = outSRI.__dict__,
            type       = self.port._using.name,
            dataBuffer = data.tolist()
            )
        self._ioloop.add_callback(self.write_message, packet)

    def write_message(self, *args, **ioargs):
        # hide WebSocketClosedError because it's very likely
        try:
            super(BulkIOWebsocketHandler, self).write_message(*args, **ioargs)
        except websocket.WebSocketClosedError:
            logging.debug('Received WebSocketClosedError. Ignoring')
            self.close()

def copy_sri(SRI):
    copied = sri.create()
    copied.hversion = SRI.hversion
    copied.xstart = SRI.xstart
    copied.xdelta = SRI.xdelta
    copied.xunits = SRI.xunits
    copied.subsize = SRI.subsize
    copied.ystart = SRI.ystart
    copied.ydelta = SRI.ydelta
    copied.yunits = SRI.yunits
    copied.mode = SRI.mode
    copied.streamID = SRI.streamID
    copied.blocking = SRI.blocking
    copied.keywords = SRI.keywords[:]
    return copied
