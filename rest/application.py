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
Rest handlers for Applications

Classes:
Applications -- Get info, launch and release
"""

from tornado import gen

from handler import JsonHandler
from helper import PropertyHelper, PortHelper

import json

class Applications(JsonHandler, PropertyHelper, PortHelper):
    @gen.coroutine
    def get(self, domain_name, app_id=None):
        try:
            if app_id:
                app = yield self.redhawk.get_application(domain_name, app_id)
                comps = yield self.redhawk.get_component_list(domain_name, app_id)
                props = app._getPropertySet()

                info = {
                    'id': app._get_identifier(),
                    'name': app.name,
                    'started': app._get_started(),
                    'components': comps,
                    'ports': self.format_ports(app.ports),
                    'properties': self.format_properties(props, app.query([]))
                }
            else:
                apps = yield self.redhawk.get_application_list(domain_name)

                info = {'applications': apps}

            self._render_json(info)
        except Exception as e:
            self._handle_request_exception(e)

    @gen.coroutine
    def post(self, domain_name, app_id=None):
        try:
            data = json.loads(self.request.body)

            if app_id:
                app = yield self.redhawk.get_application(domain_name, app_id)

                started = data['started']
                if started:
                    app.start()
                else:
                    app.stop()

                self._render_json({'id': app_id, 'started': app._get_started()})
            else:
                app_name = str(data['name'])

                app_id = yield self.redhawk.launch_application(domain_name, app_name)
                apps = yield self.redhawk.get_application_list(domain_name)

                if 'started' in data and data['started']:
                    app = yield self.redhawk.get_application(domain_name, app_id)
                    app.start()

                self._render_json({'launched': app_id, 'applications': apps})

        except Exception as e:
            self._handle_request_exception(e)

    @gen.coroutine
    def put(self, domain_name, app_id=None):
        try:
            data = json.loads(self.request.body)

            app = yield self.redhawk.get_application(domain_name, app_id)

            started = data['started']
            if started:
                app.start()
            else:
                app.stop()

            self._render_json({'id': app_id, 'started': app._get_started()})
        except Exception as e:
            self._handle_request_exception(e)

    @gen.coroutine
    def delete(self, domain_name, app_id):
        try:
            yield self.redhawk.release_application(domain_name, app_id)
            apps = yield self.redhawk.get_application_list(domain_name)

            self._render_json({'released': app_id, 'applications': apps})
            
        except Exception as e:
            self._handle_request_exception(e)

class ApplicationProperties(JsonHandler, PropertyHelper):
    @gen.coroutine
    def get(self, domain, app_id):
        try:
            app = yield self.redhawk.get_application(domain, app_id)
            props = app._getPropertySet()

            self._render_json({
                'properties': self.format_properties(props, app.query([]))
            })
        except Exception as e:
            self._handle_request_exception(e)

    @gen.coroutine
    def put(self, domain, app_id):
        try:
            data = json.loads(self.request.body)
            json_props = data.get('properties', [])
            changes = self.unformat_properties(json_props)

            yield self.redhawk.application_configure(domain, app_id, changes)
        except Exception as e:
            self._handle_request_exception(e)

