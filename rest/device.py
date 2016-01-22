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
"""
Rest handlers for Devices

Classes:
Device -- Get info of a specific device
"""

from tornado import gen

from handler import JsonHandler
from helper import PropertyHelper, PortHelper
from tornado import web
import json

class Devices(JsonHandler, PropertyHelper, PortHelper):
    @gen.coroutine
    def get(self, domainName, managerId, deviceId=None):
        if deviceId:
            dev = yield self.redhawk.get_device(domainName, managerId, deviceId)

            info = {
                'name': dev.name,
                'id': dev._id,
                'started': dev._get_started(),
                'ports': self.format_ports(dev.ports),
                'properties': self.format_properties(dev._properties)
            }
        else:
            devices = yield self.redhawk.get_device_list(domainName, managerId)
            info = {'devices': devices}

        self._render_json(info)


class DeviceProperties(JsonHandler, PropertyHelper):
    @gen.coroutine
    def get(self, domainName, managerId, deviceId):
        dev = yield self.redhawk.get_device(domainName, managerId, deviceId)

        self._render_json({
            'properties': self.format_properties(dev._properties)
        })
    
    @gen.coroutine
    def put(self, domainName, managerId, deviceId):
        PUT_METHODS = {
            'configure'     : self.redhawk.device_configure,
            'allocate'      : self.redhawk.device_allocate,
            'deallocate'    : self.redhawk.device_deallocate
        }
        data = json.loads(self.request.body)
        json_props = data.get('properties', [])
        changes = self.unformat_properties(json_props)
        
        cb = PUT_METHODS.get(data['method'], None)
        try: 
            r, message = yield cb(domainName, managerId, deviceId, changes)
            if 'configure' == data['method']:
                self._render_json({ 'method': data['method'], 'status': True , 'message': message})
            else:
                self._render_json({ 'method': data['method'], 'status': r , 'message': message})

        except Exception as e:
            self._render_json({ 'method': data['method'], 'status': False, 'message': "{0}".format(e) })