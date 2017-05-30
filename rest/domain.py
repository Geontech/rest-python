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
Rest handlers for Domains

Classes:
DomainInfo -- Get info of all or a specific domain
DomainProperties -- Manipulate the properties of a domain
"""

from tornado import gen

from handler import JsonHandler
from helper import PropertyHelper


class DomainInfo(JsonHandler, PropertyHelper):
    @gen.coroutine
    def get(self, domain_name=None, *args):
        if domain_name:
            event_channels = yield self.redhawk.get_domain_event_channels(domain_name)
            if not args:
                dom_info = yield self.redhawk.get_domain_info(domain_name)
                propertySet = yield self.redhawk.get_domain_properties(domain_name)
                apps = yield self.redhawk.get_application_list(domain_name)
                device_managers = yield self.redhawk.get_device_manager_list(domain_name)
                allocations = yield self.redhawk.get_allocation_list(domain_name)
                fs = yield self.redhawk.get_path(domain_name, '')

                info = {
                    'id': dom_info._get_identifier(),
                    'name': dom_info.name,
                    'properties': self.format_properties(propertySet, dom_info.query([])),
                    'eventChannels': event_channels,
                    'applications': apps,
                    'deviceManagers': device_managers,
                    'allocations': allocations,
                    'fs': fs
                }

        else:
            domains = yield self.redhawk.get_domain_list()
            info = {'domains': domains}
        self._render_json(info)


class DomainProperties(JsonHandler, PropertyHelper):
    @gen.coroutine
    def get(self, domain_name, prop_name=None):
        dom_info = yield self.redhawk.get_domain_info(domain_name)
        propertySet = yield self.redhawk.get_domain_properties(domain_name)
        info = self.format_properties(propertySet, dom_info.query([]))

        if prop_name:
            value = None
            for item in info:
                if item['name'] == prop_name:
                    value = item

            if value:
                self._render_json(value)
            else:
                self._render_json({'error': "Could not find property"})
        else:
            self._render_json({'properties': info})
