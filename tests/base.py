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
Base TestCase class with convenience functions
"""
__author__ = 'rpcanno'

import itertools
import time

from tornado.testing import AsyncHTTPTestCase
from tornado.httpclient import AsyncHTTPClient, HTTPRequest, HTTPResponse, HTTPError, _RequestProxy
from tornado.simple_httpclient import SimpleAsyncHTTPClient
from pyrest import Application
from tornado import gen
from tornado import httputil, stack_context
from tornado.concurrent import TracebackFuture

import json

from defaults import Default


class MyAsyncHTTPClient(SimpleAsyncHTTPClient):
  '''
     Adds a raise_error flag to fetch() to avoid exceptions when
     fetching a non-200 based response code.  This code is from the latest 4.x
     tornado which has not been released 
  '''

    
  def fetch(self, request, callback=None, raise_error=True, **kwargs):
        """Executes a request, asynchronously returning an `HTTPResponse`.

        The request may be either a string URL or an `HTTPRequest` object.
        If it is a string, we construct an `HTTPRequest` using any additional
        kwargs: ``HTTPRequest(request, **kwargs)``

        This method returns a `.Future` whose result is an
        `HTTPResponse`.  By default, the ``Future`` will raise an `HTTPError`
        if the request returned a non-200 response code. Instead, if
        ``raise_error`` is set to False, the response will always be
        returned regardless of the response code.

        If a ``callback`` is given, it will be invoked with the `HTTPResponse`.
        In the callback interface, `HTTPError` is not automatically raised.
        Instead, you must check the response's ``error`` attribute or
        call its `~HTTPResponse.rethrow` method.
        """
        if self._closed:
            raise RuntimeError("fetch() called on closed AsyncHTTPClient")
        if not isinstance(request, HTTPRequest):
            request = HTTPRequest(url=request, **kwargs)
        # We may modify this (to add Host, Accept-Encoding, etc),
        # so make sure we don't modify the caller's object.  This is also
        # where normal dicts get converted to HTTPHeaders objects.
        request.headers = httputil.HTTPHeaders(request.headers)
        request = _RequestProxy(request, self.defaults)
        future = TracebackFuture()
        if callback is not None:
            callback = stack_context.wrap(callback)

            def handle_future(future):
                exc = future.exception()
                if isinstance(exc, HTTPError) and exc.response is not None:
                    response = exc.response
                elif exc is not None:
                    response = HTTPResponse(
                        request, 599, error=exc,
                        request_time=time.time() - request.start_time)
                else:
                    response = future.result()
                self.io_loop.add_callback(callback, response)
            future.add_done_callback(handle_future)

        def handle_response(response):
            if raise_error and response.error:
                future.set_exception(response.error)
            else:
                future.set_result(response)
        self.fetch_impl(request, handle_response)
        return future

class JsonAssertions(object):

    RESPONSE_CODES_2XX = (200, 201, 202, 203, 204, 205, 206)
    RESPONSE_CODES_3XX = (300, 301, 302, 303, 304, 305, 306, 307)
    RESPONSE_CODES_4XX = (400, 401, 402, 403, 404, 405, 406, 407, 408, 409, 410, 411, 412, 413, 414, 415, 416, 417)
    RESPONSE_CODES_5XX = (500, 501, 502, 503, 504, 505)

    def assertResponse(self, response, codes=RESPONSE_CODES_2XX):
        '''
            Asserts a valid response

            Codes can be a set of codes (e.g. 2XX) or a single code
        '''
        try:
            if response.code not in codes:
                self.fail("Response code %d not one of %s", response.code, codes)
        except TypeError:
            if response.code != codes:
                self.fail("Response code %d is not %s", response.code, codes)
        

    def assertJson(self, response):
        try:
            return json.loads(response.body)
        except ValueError:
            self.fail("Unable to parse json input '%s'" % response.body)
        
    def assertJsonResponse(self, response, codes=RESPONSE_CODES_2XX):
        data = assertJson(response)
        assertResponse(response, codes)
        return data

    def assertAttr(self, data, name, value):
        self.assertTrue(name in data)
        self.assertEquals(data[name], value)

    def assertList(self, data, name):
        self.assertTrue(name in data)
        self.assertTrue(isinstance(data[name], list))

    def assertIdList(self, data, name):
        self.assertList(data, name)
        for item in data[name]:
            self.assertTrue('id' in item)
            self.assertTrue('name' in item)

    def assertProperties(self, data):
        self.assertTrue(isinstance(data, list))
        MODES = ['readwrite', 'writeonly', 'readonly']
        SCA_TYPES = ['simple', 'simpleSeq', 'struct', 'structSeq']
        for prop in data:
            # CORBA and SCA Properties have these 4 fields for certain.
            self.assertTrue('id' in prop)
            self.assertTrue('name' in prop)
            self.assertTrue('scaType' in prop)
            self.assertTrue(prop['scaType'] in SCA_TYPES)
            self.assertTrue('value' in prop)
            if prop['scaType'] != 'simple':
                self.assertList(prop, 'value')
            if prop['scaType'] in ['struct', 'structSeq']:
                self.assertProperties(prop['value'])

            # SCA Properties can be identified from CORBA ones since the former have 'kinds', among other things.
            if 'kinds' in prop:
                if prop['scaType'] in ['simple', 'simpleSeq']:
                    self.assertTrue('type' in prop)
                self.assertTrue('mode' in prop)
                self.assertTrue(prop['mode'] in MODES)



class JsonTests(AsyncHTTPTestCase, JsonAssertions):
    def get_app(self):
        return Application()

    def _json_request(self, url, code, method='GET', json_data=None):
        body = None
        if json_data:
            body = json.dumps(json_data)

        AsyncHTTPClient(self.io_loop).fetch(self.get_url(Default.REST_BASE+url), self.stop, method=method, body=body)
        response = self.wait()

        self.assertEquals(code, response.code)

        data = {}
        if response.body:
            data = json.loads(response.body)

        return data, response
    
    @gen.coroutine    
    def _async_json_request(self, url, code, method='GET', json_data=None):
        '''
            Like _json_request, but yields a future
            Use like:
            @tornado.testing.gen_test
            test_foo(self):
                 json, resp = yield_async_json_request('foo/bar')
                 self.assertEquals('bar', json['value'])
            
        '''         
        body = None
        if json_data:
            body = json.dumps(json_data)

        response = yield MyAsyncHTTPClient(self.io_loop).fetch(self.get_url(Default.REST_BASE+url), self.stop, method=method, body=body, raise_error=False)        
        self.assertEquals(code, response.code)

        data = {}
        if response.body:
            data = json.loads(response.body)

        raise gen.Return((data, response))
    
    @gen.coroutine
    def _async_set_property(self, comp_id, d={}, **kwargs):
        '''
            resp = yield _async_set_property(id, name=value, name=value)
               or
            resp = yield _async_set_property(id, {'foo:bar': 123})
               
        '''
        json, resp = yield self._async_json_request(
            "%s/components/%s/properties" % (self.base_url, comp_id), 200, 'PUT',
            {'properties': [ 
               {'id': p[0], 'value': p[1]} for p in itertools.chain(d.items(), kwargs.items())
             ]}
          )
        raise gen.Return(resp)
        
    @gen.coroutine
    def _async_get_properties(self, comp_id):
        '''
            Gets the properties asynchronously.  Properties is a dictionary of the returned
            properties.  
            
            properties, resp = yield _async_get_properties(comp_id)
        '''
        json, resp = yield self._async_json_request("%s/components/%s/properties" % (self.base_url, comp_id), 200)
        raise gen.Return((dict((p["id"], p["value"]) for p in json['properties']), resp))
    
    
    @gen.coroutine
    def _async_sleep(self, seconds):
        '''
            Sleeps this request in the ioloop for seconds seconds.
            Usage:
               yield task1()
               yield _async_sleep(.5)
               yield task2()
               
        '''
        yield gen.Task(self.io_loop.add_timeout, time.time() + seconds)



    def _resource_not_found(self, body):
        self.assertTrue('error' in body)
        self.assertEquals(body['error'], Default.RESOURCE_NOT_FOUND_ERR)
        self.assertTrue('message' in body)
        self.assertTrue(Default.RESOURCE_NOT_FOUND_MSG_REGEX.match(body['message']))
