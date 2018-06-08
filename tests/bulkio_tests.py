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

# system imports
import unittest
import json
import logging
import time
import threading
from functools import partial

# tornado imports
import tornado
import tornado.testing
from tornado.testing import AsyncHTTPTestCase, LogTrapTestCase
from tornado.httpclient import AsyncHTTPClient, HTTPRequest
from tornado import websocket, gen

# application imports
from pyrest import Application
from base import JsonTests
from defaults import Default

# all method returning suite is required by tornado.testing.main()
#def all():
#   return unittest.TestLoader().loadTestsFromModule(__import__(__name__))


class BulkIOTests(JsonTests, AsyncHTTPTestCase, LogTrapTestCase):

    def setUp(self):
        super(JsonTests, self).setUp()
        json_msg, resp = self._json_request(
            '/domains/%s/applications' % Default.DOMAIN_NAME,
            200,
            'POST',
            {'name': Default.WAVEFORM, 'started': True }
        )
        self.assertTrue('launched' in json_msg)
        self.base_url = '/domains/%s/applications/%s' % (Default.DOMAIN_NAME, json_msg['launched'])
        json_msg, resp = self._json_request(self.base_url, 200)

        self.assertIn('started', json_msg)
        self.assertTrue(json_msg['started'])
        self.assertList(json_msg, 'components')
        self.assertTrue(json_msg['components'])
        self.components = json_msg['components']

    def tearDown(self):
        self._json_request(
            self.base_url,
            200,
            'DELETE'
        )
        super(BulkIOTests, self).tearDown()



    def get_app(self):
        return Application(debug=True, _ioloop=self.io_loop)

    @tornado.gen.coroutine
    def _get_connection(self):
        cid = next(
            (cp['id'] for cp in self.components if cp['name'] == Default.COMPONENT), None)
        if not cid:
            self.fail('Unable to find %s component' % (Default.COMPONENT))

        url = self.get_url("%s/components/%s/ports/%s/bulkio" % (Default.REST_BASE +
                                                                 self.base_url, cid, Default.COMPONENT_USES_PORT)).replace('http', 'ws')
        logging.debug('WS URL: ' + url)
        conn = yield websocket.websocket_connect(url, io_loop=self.io_loop)
        raise tornado.gen.Return(conn)

    @tornado.testing.gen_test
    def test_bulkio_ws(self):
        # NOTE: A timeout means the website took too long to respond
        # it could mean that bulkio port is not sending data
        conn = yield self._get_connection()

        foundSRI = False
        for x in xrange(10):
            msg = yield conn.read_message()
            try:
                packet = json.loads(msg)
                sri = packet.get('SRI', None)
                logging.debug("Got SRI %s", sri)
                foundSRI = True
                props = set(('hversion', 'xstart', 'xdelta', 'xunits',
                            'subsize', 'ystart', 'ydelta', 'yunits', 'mode',
                            'streamID', 'blocking', 'keywords'))
                missing = props.difference(sri.keys())
                if missing:
                    self.fail("Missing SRI properties %s" % missing)

                buf = packet.get('dataBuffer', [])
                if not buf:
                    self.fail("Data buffer was empty.")

            except ValueError:
                data = dict(data=msg)

        if packet.get('error', None):
            self.fail('Recieved websocket error %s' % packet)
        conn.close()

        # wait a little bit to force close to take place in ioloop
        # (if we return without waiting, ioloop closes before websocket closes)
        x = yield gen.Task(self.io_loop.add_timeout, time.time() + .5)

        if not foundSRI:
            self.fail('Did not receive SRI')

    @tornado.testing.gen_test
    def test_sri_keywords_ws(self):
        # NOTE: A timeout means the website took too long to respond
        # it could mean that bulkio port is not sending data
        cid = next(
            (cp['id'] for cp in self.components if cp['name'] == Default.COMPONENT), None)
        if not cid:
            self.fail('Unable to find %s component' % (Default.COMPONENT))

        url = self.get_url("%s/components/%s/ports/%s/bulkio" % (Default.REST_BASE +
            self.base_url, cid, Default.COMPONENT_USES_PORT)).replace('http', 'ws')
        conn1 = yield websocket.websocket_connect(url, io_loop=self.io_loop)

        # Check SRI behavior (changed = true, kewords)
        # Configure the siggen's col_rf property
        change_fails = 0
        change_fails_limit = 100
        keyword_fails = 0
        keyword_fails_limit = 100
        col_rf = 100
        col_rf_limit = 200
        d, r = yield self._async_json_request(
            "%s/components/%s/properties" % (self.base_url, cid),
            200,
            'PUT',
            {'properties': [
                {'id': Default.COMPONENT_COL_RF, 'value': col_rf}
            ]}
        )

        while True:
            msg = yield conn1.read_message()
            try:
                packet = json.loads(msg)
                self.assertIn('sriChanged', packet)
                sriChanged = packet.get('sriChanged', False)
                if not sriChanged:
                    change_fails += 1
                    if change_fails <= change_fails_limit:
                        continue;
                    else:
                        self.fail("SRI did not change within {0} pushes".format(
                            change_fails_limit))
                        break
                logging.info('SRI Changed detected')

                # Verify the change is what we expected, COL_RF keyword
                self.assertIn('SRI', packet)
                sri = packet.get('SRI', {})
                self.assertIn('keywords', sri)
                keywords = sri.get('keywords', {})
                self.assertIn('COL_RF', keywords)
                new_col_rf = int(keywords.get('COL_RF', 0))

                logging.info('SRI: {0}'.format(sri))
                logging.info('keywords: {0}'.format(keywords))

                if col_rf != new_col_rf:
                    keyword_fails += 1
                    if keyword_fails > keyword_fails_limit:
                        self.fail("SRI Keyword did not update ({0} vs. {1})".format(
                            col_rf, new_col_rf
                        ))
                else:
                    logging.debug("Received updated SRI Keyword COL_RF: {0}".format(new_col_rf))
                    if new_col_rf == col_rf_limit:
                        # Time to quit successfully!
                        break;
                    else:
                        logging.info('Changing COL_RF to change SRI')
                        change_fails = 0
                        keyword_fails = 0
                        col_rf = col_rf_limit
                        d, r = yield self._async_json_request(
                            "%s/components/%s/properties" % (self.base_url, cid),
                            200,
                            'PUT',
                            {'properties': [
                                {'id': Default.COMPONENT_COL_RF, 'value': col_rf}
                            ]}
                        )

            except ValueError:
                data = dict(data=msg)

        if packet.get('error', None):
            self.fail('Recieved websocket error %s' % packet)
        conn1.close()

        # wait a little bit to force close to take place in ioloop
        # (if we return without waiting, ioloop closes before websocket closes)
        x = yield gen.Task(self.io_loop.add_timeout, time.time() + .5)


if __name__ == '__main__':

    tornado.testing.main()

