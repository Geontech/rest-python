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
                        data_type = p._using.name
                        namespace = p._using.nameSpace

                        if namespace == 'BULKIO':
                            self.port = p.ref
                            logging.debug("Found port %s", self.port)

                            bulkio_poa = getattr(BULKIO__POA, data_type)
                            logging.debug(bulkio_poa)

                            self.async_port = AsyncPort(bulkio_poa, self._pushSRI, self._pushPacket)
                            self._portname = 'rest-python-%s' % id(self)

                            if len(path) == 3:
                                self._connectionId = path[2][1:]
                            else:
                                self._connectionId = None

                            self.port.connectPort(self.async_port.getPort(), self._portname, self._connectionId)

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
        ctrl = json.loads(message)

        if (ctrl.type == Control.MaxWidth):
            if 0 < ctrl.value:
                self._outputWidth = ctrl.value
                logging.info('Decimation requested to {0} samples'.format(ctrl.value))
            else:
                self._outputWidth = None
                logging.info('Decimation disabled')

        elif (ctrl.type == Control.MaxPPS):
            logging.warning('Packets per second (PPS) not implemented yet.')

    def on_close(self):
        logging.debug('Stream CLOSE')
        try:
            self.port.disconnectPort(self._portname, self._connectionId)
        except CORBA.TRANSIENT:
            pass 
        except Exception, e:
            logging.exception('Error disconnecting port %s' % self._portname)

    def _pushSRI(self, SRI):
        newSri = dict(
            hversion=SRI.hversion,
            xstart=SRI.xstart,
            xdelta=SRI.xdelta,
            xunits=SRI.xunits,
            subsize=SRI.subsize,
            ystart=SRI.ystart,
            ydelta=SRI.ydelta,
            yunits=SRI.yunits,
            mode=SRI.mode,
            streamID=SRI.streamID,
            blocking=SRI.blocking,
            keywords=dict(((kw.id, kw.value.value()) for kw in SRI.keywords)))
        self._updateSRIFromDict(newSri)

    def _getSRI(self, streamID):
        return self._SRIs.get(streamID, (None, True))

    def _updateSRIFromDict(self, newSri):
        sri, changed = self._getSRI(newSri['streamID'])
        if sri is not None:
            changed = compareSRI(sri, newSri)
        self._SRIs[sri.streamID] = (newSri, changed)

    def _pushPacket(self, data, ts, EOS, stream_id):
        data = numpy.array(data)

        if None == self._outputWidth:
            self._outputWidth = data.size 

        # Get SRI and modify if necessary (from decimation)
        sri, changed = self._getSRI(stream_id)
        outSri = dict.copy(sri)
        if 0 < data.size and data.size != self._outputWidth:
            D, M = divmod(data.size, self._outputWidth)
            if 0 == M and 1 < D:
                # Mean decimate
                data = data.reshape(-1, D).mean(axis=1)
                outSri.xdelta = sri.xdelta * D
                changed = True
            else:
                # Restore...invalid setting.
                # TODO: Support interp+decimate rather than just
                #       neighbor-mean
                logging.warning('Interpolate+decimate not supported.  Restoring original output width.')
                self._outputWidth = None

        # Tack on SRI, Package, Deliver.
        packet = dict(
            streamID   = stream_id,
            T          = ts,
            EOS        = EOS,
            sriChanged = changed,
            SRI        = outSri,
            type       = self.port._using.name,
            dataBuffer = data
            )
        self._ioloop.add_callback(self.write_message, packet)

    def write_message(self, *args, **ioargs):
        # hide WebSocketClosedError because it's very likely
        try:
            super(BulkIOWebsocketHandler, self).write_message(*args, **ioargs)
        except websocket.WebSocketClosedError:
            logging.debug('Received WebSocketClosedError. Ignoring')
            self.close()

# Imported from ossie.utils sb
# TODO: Handle keywords JSON strings
def compareSRI(a, b):
    if a.hversion != b.hversion:
        return False
    if a.xstart != b.xstart:
        return False
    if a.xdelta != b.xdelta:
        return False
    if a.xunits != b.xunits:
        return False
    if a.subsize != b.subsize:
        return False
    if a.ystart != b.ystart:
        return False
    if a.ydelta != b.ydelta:
        return False
    if a.yunits != b.yunits:
        return False
    if a.mode != b.mode:
        return False
    if a.streamID != b.streamID:
        return False
    if a.blocking != b.blocking:
        return False
    if a.keywords != b.keywords:
        return False
    return True