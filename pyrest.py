#!/usr/bin/env python
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
import os

from rest.domain import DomainInfo, DomainProperties
from rest.waveform import Waveforms
from rest.component import Component, ComponentProperties
from rest.devicemanager import DeviceManagers
from rest.device import Device, DeviceProperties
from rest.fei import FEITunerHandler, FEIRFInfoHandler, FEIRFSourceHandler, FEIGPSHandler, FEINavDataHandler
from rest.port import PortHandler
from rest.bulkio_handler import BulkIOWebsocketHandler

import tornado.httpserver
import tornado.web
import tornado.websocket
from tornado import ioloop

from model.redhawk import Redhawk

# setup command line options
from tornado.options import define, options

define('port', default=8080, type=int, help="server port")
define("debug", default=False, type=bool, help="Enable Tornado debug mode.  Reloads code")

_ID = r'/([^/]+)'
_LIST = r'/?'
_DOMAIN_PATH = r'/rh/rest/domains'
_WAVEFORM_PATH = _DOMAIN_PATH + _ID + r'/waveforms'
_COMPONENT_PATH = _WAVEFORM_PATH + _ID + r'/components'
_DEVICE_MGR_PATH = _DOMAIN_PATH + _ID + r'/deviceManagers'
_DEVICE_PATH = _DEVICE_MGR_PATH + _ID + r'/devices'
_PROPERTIES_PATH = r'/properties'
_PORT_PATH = r'/ports'
_FEI_TUNER_ID = r'/([^/]+Tuner[^/]+)'
_FEI_RFINFO_ID = r'/(RFInfo[^/]+)'
_FEI_RFSOURCE_ID = r'/(RFSource[^/]+)'
_FEI_GPS_ID = r'/(GPS[^/]+)'
_FEI_NAVDATA_ID = r'/(NavData[^/]+)'
_BULKIO_PATH = _PORT_PATH + _ID + r'/bulkio'


class Application(tornado.web.Application):
    def __init__(self, *args, **kwargs):
        # explicit _ioloop for unit testing
        _ioloop = kwargs.get('_ioloop', None)
        cwd = os.path.abspath(os.path.dirname(__import__(__name__).__file__))

        # REDHAWK Service
        redhawk = Redhawk()

        handlers = [
            (r"/apps/(.*)/$", IndexHandler),
            (r"/apps/(.*)", tornado.web.StaticFileHandler, {"path": os.path.join(cwd, "apps")}),
            (r"/client/(.*)", tornado.web.StaticFileHandler, {"path": os.path.join(cwd, "client")}),

            # Domains
            (_DOMAIN_PATH + _LIST, DomainInfo, dict(redhawk=redhawk)),
            (_DOMAIN_PATH + _ID, DomainInfo, dict(redhawk=redhawk)),
            (_DOMAIN_PATH + _ID + _PROPERTIES_PATH + _LIST, DomainProperties, dict(redhawk=redhawk)),
            (_DOMAIN_PATH + _ID + _PROPERTIES_PATH + _ID, DomainProperties, dict(redhawk=redhawk)),

            # Waveforms
            (_WAVEFORM_PATH + _LIST, Waveforms, dict(redhawk=redhawk)),
            (_WAVEFORM_PATH + _ID, Waveforms, dict(redhawk=redhawk)),
            (_WAVEFORM_PATH + _ID + _PORT_PATH + _LIST, PortHandler, dict(kind='waveform')),
            (_WAVEFORM_PATH + _ID + _PORT_PATH + _ID, PortHandler, dict(kind='waveform')),
            (_WAVEFORM_PATH + _ID + _BULKIO_PATH, BulkIOWebsocketHandler, dict(kind='waveform', _ioloop=_ioloop)),

            # Components
            (_COMPONENT_PATH + _LIST, Component, dict(redhawk=redhawk)),
            (_COMPONENT_PATH + _ID, Component, dict(redhawk=redhawk)),
            (_COMPONENT_PATH + _ID + _PROPERTIES_PATH + _LIST, ComponentProperties, dict(redhawk=redhawk)),
            (_COMPONENT_PATH + _ID + _PROPERTIES_PATH + _ID, ComponentProperties, dict(redhawk=redhawk)),
            (_COMPONENT_PATH + _ID + _PORT_PATH + _LIST, PortHandler, dict(kind='component')),
            (_COMPONENT_PATH + _ID + _PORT_PATH + _ID, PortHandler, dict(kind='component')),
            (_COMPONENT_PATH + _ID + _BULKIO_PATH, BulkIOWebsocketHandler, dict(kind='component', _ioloop=_ioloop)),

            # Device Managers
            (_DEVICE_MGR_PATH + _LIST, DeviceManagers, dict(redhawk=redhawk)),
            (_DEVICE_MGR_PATH + _ID, DeviceManagers, dict(redhawk=redhawk)),

            # Devices
            (_DEVICE_PATH + _LIST, Device, dict(redhawk=redhawk)),
            (_DEVICE_PATH + _ID, Device, dict(redhawk=redhawk)),
            (_DEVICE_PATH + _ID + _PROPERTIES_PATH + _LIST, DeviceProperties, dict(redhawk=redhawk)),
            (_DEVICE_PATH + _ID + _PROPERTIES_PATH + _ID, DeviceProperties, dict(redhawk=redhawk)),
            (_DEVICE_PATH + _ID + _PORT_PATH + _LIST, PortHandler, dict(kind='device')),
            (_DEVICE_PATH + _ID + _PORT_PATH + _FEI_TUNER_ID + _LIST, FEITunerHandler, dict(redhawk=redhawk)),
            (_DEVICE_PATH + _ID + _PORT_PATH + _FEI_TUNER_ID + _ID + _LIST, FEITunerHandler, dict(redhawk=redhawk)),
            (_DEVICE_PATH + _ID + _PORT_PATH + _FEI_TUNER_ID + _ID + _ID, FEITunerHandler, dict(redhawk=redhawk)),
            (_DEVICE_PATH + _ID + _PORT_PATH + _FEI_RFINFO_ID + _LIST, FEIRFInfoHandler, dict(redhawk=redhawk)),
            (_DEVICE_PATH + _ID + _PORT_PATH + _FEI_RFINFO_ID + _ID, FEIRFInfoHandler, dict(redhawk=redhawk)),
            (_DEVICE_PATH + _ID + _PORT_PATH + _FEI_RFSOURCE_ID + _LIST, FEIRFSourceHandler, dict(redhawk=redhawk)),
            (_DEVICE_PATH + _ID + _PORT_PATH + _FEI_RFSOURCE_ID + _ID, FEIRFSourceHandler, dict(redhawk=redhawk)),
            (_DEVICE_PATH + _ID + _PORT_PATH + _FEI_GPS_ID + _LIST, FEIGPSHandler, dict(redhawk=redhawk)),
            (_DEVICE_PATH + _ID + _PORT_PATH + _FEI_GPS_ID + _ID, FEIGPSHandler, dict(redhawk=redhawk)),
            (_DEVICE_PATH + _ID + _PORT_PATH + _FEI_NAVDATA_ID + _LIST, FEINavDataHandler, dict(redhawk=redhawk)),
            (_DEVICE_PATH + _ID + _PORT_PATH + _FEI_NAVDATA_ID + _ID, FEINavDataHandler, dict(redhawk=redhawk)),  
            (_DEVICE_PATH + _ID + _PORT_PATH + _ID, PortHandler, dict(kind='device')), # Default port handler
            (_DEVICE_PATH + _ID + _BULKIO_PATH, BulkIOWebsocketHandler, dict(kind='device', _ioloop=_ioloop)),
        ]
        tornado.web.Application.__init__(self, handlers, *args, **kwargs)


class IndexHandler(tornado.web.RequestHandler):
    def get(self, path):
        self.render("apps/"+path+"/index.html")


def main():
    tornado.options.parse_command_line()
    application = Application(debug=options.debug)
    application.listen(options.port)
    ioloop.IOLoop.instance().start()

if __name__ == '__main__':
    main()

