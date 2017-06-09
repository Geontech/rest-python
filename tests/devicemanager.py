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
Tornado tests for the /domain/{NAME}/deviceManagers portion of the REST API
"""
__author__ = 'rpcanno'

from base import JsonTests

from defaults import Default


class DeviceManagerTests(JsonTests):
    def _get_dev_mgr_list(self):
        """
        Get a list of device managers from one level up (ie the control)
        """
        body, resp = self._json_request("/domains/"+Default.DOMAIN_NAME, 200)

        self.assertTrue('deviceManagers' in body)
        self.assertTrue(isinstance(body['deviceManagers'], list))

        return body['deviceManagers']

    def test_list(self):
        dev_managers = self._get_dev_mgr_list()

        body, resp = self._json_request("/domains/"+Default.DOMAIN_NAME+"/deviceManagers", 200)

        self.assertTrue('deviceManagers' in body)
        self.assertTrue(isinstance(body['deviceManagers'], list))

        for mgr in body['deviceManagers']:
            self.assertTrue('id' in mgr)
            self.assertTrue('name' in mgr)
            
        self.assertEquals(dev_managers, body['deviceManagers'])

    def test_info(self):
        dev_managers = self._get_dev_mgr_list()

        self.assertTrue(len(dev_managers) > 0)

        mgr = dev_managers[0]
        self.assertTrue('id' in mgr)

        body, resp = self._json_request("/domains/"+Default.DOMAIN_NAME+"/deviceManagers/"+mgr['id'], 200)

        self.assertTrue('name' in body)
        self.assertEquals(body['name'], mgr['name'])
        self.assertTrue('id' in body)
        self.assertEquals(body['id'], mgr['id'])

        self.assertTrue('services' in body)
        self.assertTrue('properties' in body)
        self.assertTrue('devices' in body)

    def test_info_not_found(self):
        body, resp = self._json_request("/domains/"+Default.DOMAIN_NAME+"/deviceManagers/sdkafsdfhklasdfhkajl", 404)
