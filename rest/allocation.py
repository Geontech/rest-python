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
Rest handlers for Allocations

Classes:
Allocations -- Get info
"""

from tornado import gen

from handler import JsonHandler
from helper import PropertyHelper

import json


class Allocations(JsonHandler, PropertyHelper):
    @gen.coroutine
    def get(self, domain_name, allocation_id=None):
        try:
            if allocation_id:
                allocation = yield self.redhawk.get_allocation(domain_name, allocation_id)

                info = {
                    'id': allocation.allocationID,
                    'deviceId': allocation.allocatedDevice._get_identifier(),
                    'deviceManagerId': allocation.allocationDeviceManager._get_identifier(),
                    'properties': self.format_properties(allocation.allocationProperties),
                    'sourceId': allocation.sourceID
                }
            else:
                allocations = yield self.redhawk.get_allocation_list(domain_name)

                info = {'allocations': allocations}

            self._render_json(info)
        except Exception as e:
            self._handle_request_exception(e)

    @gen.coroutine
    def post(self, domain_name, *args):
        try:
            data = json.loads(self.request.body)
            json_device_ids = data.get('deviceIds', [])
            json_props = data.get('properties', [])
            json_source_id = data.get('sourceId', '')
            props = self.unformat_properties_without_query(json_props)

            if 'allocationId' in data:
                allocation_id = data['allocationId']
            else:
                raise Exception('ALLOCATION_ID is required for allocations.')

            allocation_id = yield self.redhawk.allocate(domain_name, allocation_id, json_device_ids, props, json_source_id)
            allocations = yield self.redhawk.get_allocation_list(domain_name)

            self._render_json({'allocated': allocation_id, 'allocations': allocations})

        except Exception as e:
            self._handle_request_exception(e)

    @gen.coroutine
    def delete(self, domain_name, *args):
        try:
            data = json.loads(self.request.body)
            allocation_ids = data.get('allocationIds', [])

            yield self.redhawk.deallocate(domain_name, allocation_ids)
            allocations = yield self.redhawk.get_allocation_list(domain_name)

            info = {
                'deallocated': allocation_ids,
                'allocations': allocations
            }

            self._render_json(info)
            
        except Exception as e:
            self._handle_request_exception(e)
