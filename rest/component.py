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
Rest handlers for Components

Classes:
Component -- Get info about a specific component
ComponentProperties -- Manipulate properties of a specific component
"""
from tornado import gen

from handler import JsonHandler
from helper import PropertyHelper, PortHelper

import json


class Components(JsonHandler, PropertyHelper, PortHelper):
    @gen.coroutine
    def get(self, domain_name, app_id, comp_id=None):
        try:
            if comp_id:
                comp = yield self.redhawk.get_component(domain_name, app_id, comp_id)

                info = {
                    'name': comp.name,
                    'id': comp._id,
                    'started': comp._get_started(),
                    'ports': self.format_ports(comp.ports),
                    'properties': self.format_properties(comp._properties, comp.query([]))
                }
            else:
                comps = yield self.redhawk.get_component_list(domain_name, app_id)
                info = {'components': comps}

            self._render_json(info)
        except Exception as e:
            self._handle_request_exception(e)


class ComponentProperties(JsonHandler, PropertyHelper):
    @gen.coroutine
    def get(self, domain, application, component):
        try:
            comp = yield self.redhawk.get_component(domain, application, component)

            self._render_json({
                'properties': self.format_properties(comp._properties, comp.query([]))
            })
        except Exception as e:
            self._handle_request_exception(e)

    @gen.coroutine
    def put(self, domain, application, component):
        try:
            data = json.loads(self.request.body)
            json_props = data.get('properties', [])
            changes = self.unformat_properties(json_props)

            yield self.redhawk.component_configure(domain, application, component, changes)
        except Exception as e:
            self._handle_request_exception(e)
