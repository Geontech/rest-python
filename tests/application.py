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
Tornado tests for the /domain/{NAME}/applications portion of the REST API
"""

import tornado

from base import JsonTests
from defaults import Default
from model.redhawk import Redhawk


class ApplicationTests(JsonTests):
    
    def setUp(self):
        super(ApplicationTests, self).setUp();
        self.redhawk = Redhawk()

    def tearDown(self):
        # kill SigTest waveforms
        dom = self.redhawk._get_domain(Default.DOMAIN_NAME)
        apps = dom.find_app()
        for app in apps:
            if app.name.startswith(Default.WAVEFORM):
                app.releaseObject()
        super(ApplicationTests, self).tearDown();
    
    @tornado.gen.coroutine
    def _get_applications(self):
        url = '/domains/'+Default.DOMAIN_NAME
        json, resp = yield self._async_json_request(url, 200)

        self.assertTrue('applications' in json)

        raise tornado.gen.Return((url, json['applications']))

    @tornado.gen.coroutine
    def _launch(self, name):
        json, resp = yield self._async_json_request(
            '/domains/'+Default.DOMAIN_NAME+'/applications',
            200,
            'POST',
            {'name': name}
        )
        self.assertTrue('launched' in json)
        self.assertTrue('applications' in json)
        self.assertTrue(json['launched'] in [x['id'] for x in json['applications']])

        raise tornado.gen.Return(json['launched'])

    @tornado.gen.coroutine
    def _release(self, wf_id):
        json, resp = yield self._async_json_request(
            '/domains/'+Default.DOMAIN_NAME+'/applications/'+wf_id,
            200,
            'DELETE'
        )

        self.assertAttr(json, 'released', wf_id)

        self.assertTrue('applications' in json)
        self.assertFalse(json['released'] in json['applications'])
        raise tornado.gen.Return(resp)

    @tornado.testing.gen_test
    def test_launch_release(self):
        '''
        This test checks that a launched waveform does in-fact exist in the
        applications endpoint as well as is removed once released.
        '''
        wf_id = yield self._launch(Default.WAVEFORM)
        url, applications = yield self._get_applications()
        self.assertTrue(any([Default.WAVEFORM in x['name'] for x in applications]))
        yield self._release(wf_id)

    @tornado.testing.gen_test
    def test_list(self):
        url = '/domains/' + Default.DOMAIN_NAME
        json, resp = yield self._async_json_request(url, 200)

        self.assertTrue('waveforms' in json)
        self.assertTrue(isinstance(json['waveforms'], list))
        for app in json['waveforms']:
            self.assertTrue('sad' in app)
            self.assertTrue('name' in app)

        self.assertIdList(json, 'applications')

    @tornado.testing.gen_test
    def test_info(self):
        wf_id = yield self._launch(Default.WAVEFORM)

        url = '/domains/%s/applications/%s' % (Default.DOMAIN_NAME, wf_id)
        json, resp = yield self._async_json_request(url, 200)

        self.assertList(json, 'ports')
        self.assertList(json, 'components')
        self.assertTrue('name' in json)
        self.assertAttr(json, 'id', wf_id)

        self.assertList(json, 'properties')
        self.assertProperties(json['properties'])
        
        
    @tornado.testing.gen_test
    def test_not_found(self):
        url = '/domains/%s/applications/adskfhsdhfasdhjfhsd' %Default.DOMAIN_NAME
        json, resp = yield self._async_json_request(url, 404)
    
