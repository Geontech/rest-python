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
REDHAWK Helper class used by the Server Handlers
"""

import logging
from ossie.cf import StandardEvent  # For the EventHelper
from ossie.utils import redhawk
from ossie.events import GenericEventConsumer
import traceback

from tornado.websocket import WebSocketClosedError

from functools import partial
import uuid


def scan_domains():
    return redhawk.scan()

class ResourceNotFound(Exception):
    def __init__(self, resource='resource', name='Unknown'):
        self.name = name
        self.resource = resource

    def __str__(self):
        return "Unable to find %s '%s'" % (self.resource, self.name)


class WaveformLaunchError(Exception):
    def __init__(self, name='Unknown', msg=''):
        self.name = name
        self.msg = msg

    def __str__(self):
        return "Not able to launch waveform '%s'. %s" % (self.name, self.msg)


class ApplicationReleaseError(Exception):
    def __init__(self, name='Unknown', msg=''):
        self.name = name
        self.msg = msg

    def __str__(self):
        return "Not able to release waveform '%s'. %s" % (self.name, self.msg)

# Helper class to convert the enumeration fields to something JSON serializable
class EventHelper(object):
    ENUM_MAP = {
        'sourceCategory'      : [str(i) for i in StandardEvent.SourceCategoryType._items],
        'stateChangeCategory' : [str(i) for i in StandardEvent.StateChangeCategoryType._items],
        'stateChangeFrom'     : [str(i) for i in StandardEvent.StateChangeType._items],
        'stateChangeTo'       : [str(i) for i in StandardEvent.StateChangeType._items],
        }

    @staticmethod
    # event is a python dictionary, the result of from_any() in GenericEventConsumer.
    def format_event(event):
        for k in event:
            if type(k) == dict:
                EventHelper.format_event(k)
            elif 'sourceIOR' == k:
                event[k] = 'OBJECT_REFERENCE'
            elif k in EventHelper.ENUM_MAP:
                v = event[k]
                event[k] = {
                    'value'        : str(v),
                    'enumerations' : EventHelper.ENUM_MAP[k]
                    }
        return event


class GenericEventConsumerMultiplexer (GenericEventConsumer):
    __registration_id = None

    def __init__(self, domain, on_disconnect=None, filter=None, keep_structs=None):
        GenericEventConsumer.__init__(self, self.multiplex_deliver, on_disconnect, filter, keep_structs)
        self.__listeners = []
        self.__domain = domain
        self.__registration_id = domain + str(uuid.uuid4())

    @property
    def registration_id(self):
        return self.__registration_id
    

    def multiplex_deliver(self, event, typecode):
        # TODO: Move this 'attempt' logic into the callback so that it returns true if successful
        # and false if not.
        def attempt(callback, msg):
            try:
                callback(msg)
                return True
            except WebSocketClosedError as e:
                return False

        message = { 
            'domain'  : self.__domain, 
            'event'   : EventHelper.format_event(event)
            }
        self.__listeners[:] = [cb for cb in self.__listeners if attempt(cb, message)]

    def add_listener(self, callbackFn):
        if callbackFn not in self.__listeners:
            self.__listeners.append(callbackFn)

    def rm_listener(self, callbackFn):
        self.__listeners[:] = [cb for cb in self.__listeners if callbackFn != cb]


class Domain:
    domMgr_ptr = None
    odmListener = None
    eventHandlers = None
    name = None

    def __init__(self, domainname):
        logging.trace("Establishing domain %s", domainname, exc_info=True)
        self.name = domainname
        self.eventHandlers = {}
        try:
            self._establish_domain()
        except StandardError, e:
            logging.warn("Unable to find domain %s", e, exc_info=1)
            raise ResourceNotFound("domain", domainname)

    def __del__(self):
        if self.domMgr_ptr and self.eventHandlers:
            for k, v in self.eventHandlers.items():
                self.domMgr_ptr.unregisterFromEventChannel(v.registration_id, k)

    def disconnect(self):
        old = dict(self.eventHandlers)
        for topic in old:
            self.channel_disconnected(topic)

    def channel_disconnected(self, topic):
        if topic in self.eventHandlers:
            self.domMgr_ptr.unregisterFromEventChannel(self.eventHandlers[topic].registration_id, topic)
            del self.eventHandlers[topic]

    def add_event_listener(self, callbackFn, topic):
        if topic not in self.eventHandlers:
            handler = GenericEventConsumerMultiplexer(self.name, partial(self.channel_disconnected, topic))
            self.domMgr_ptr.registerWithEventChannel(handler._this(), handler.registration_id, str(topic))
            self.eventHandlers[topic] = handler
        self.eventHandlers[topic].add_listener(callbackFn)


    def rm_event_listener(self, callbackFn, topic=None):
        if not topic:
            for k in self.eventHandlers:
                self.rm_event_listener(callbackFn, k)
        else:
            self.eventHandlers[topic].rm_listener(callbackFn);

    def _establish_domain(self):
        redhawk.setTrackApps(False)
        self.domMgr_ptr = redhawk.attach(str(self.name))

    def properties(self):
        props = self.domMgr_ptr.query([])  # TODO: self.domMgr_ptr._properties
        return props

    def event_channels(self):
        return ['ODM_Channel', 'IDM_Channel'] # TODO: Check the event service for names.

    def get_domain_info(self):
        if self.domMgr_ptr:
            return self.domMgr_ptr
        raise ResourceNotFound('domain', self.name)

    def find_app(self, app_id=None):
        _dom = self.get_domain_info()
        apps = _dom.apps

        if not app_id:
            return apps

        for app in apps:
            if app._get_identifier() == app_id:
                return app
        raise ResourceNotFound('application', app_id)

    def find_component(self, app_id, comp_id=None):
        app = self.find_app(app_id)

        if not comp_id:
            return app.comps

        for comp in app.comps:
            if comp._id == comp_id:
                return comp
        raise ResourceNotFound('component', comp_id)

    def find_device_manager(self, device_manager_id=None):
        _dom = self.get_domain_info()

        if not device_manager_id:
            return _dom.devMgrs

        for dev_mgr in _dom.devMgrs:
            if dev_mgr.id == device_manager_id:
                return dev_mgr
        raise ResourceNotFound('device manager', device_manager_id)

    def find_device(self, device_manager_id, device_id=None):
        dev_mgr = self.find_device_manager(device_manager_id)

        if not device_id:
            return dev_mgr.devs

        for dev in dev_mgr.devs:
            if dev._id == device_id:
                return dev
        raise ResourceNotFound('device', device_id)

    def find_service(self, device_manager_id, service_id=None):
        dev_mgr = self.find_device_manager(device_manager_id)

        if not service_id:
            return dev_mgr.services

        for svc in dev_mgr.services:
            if svc.id == service_id:
                return svc
        raise ResourceNotFound('service', service_id)

    def apps(self):
        apps_dict = []
        apps = self.find_app()
        for app in apps:
            apps_dict.append({'name': app.name, 'id': app._get_identifier()})
        return apps_dict

    def components(self, app_id):
        comps_dict = []
        comps = self.find_component(app_id)
        for comp in comps:
            comps_dict.append({'name': comp.name, 'id': comp._get_identifier()})
        return comps_dict

    def launch(self, app_name):
        _dom = self.get_domain_info()
        try:
            app = _dom.createApplication(app_name)
            return app._get_identifier()
        except Exception, e:
            raise WaveformLaunchError(app_name, str(e))

    def release(self, app_id):
        app = self.find_app(app_id)
        try:
            app.releaseObject()
            return app_id
        except Exception, e:
            raise ApplicationReleaseError(app_id, str(e))

    def available_apps(self):
        _dom = self.get_domain_info()
        sads_full_path = _dom.catalogSads()
        sads = _dom._sads
        sad_ret = []
        for idx in range(len(sads)):
            sad_ret.append({'name': sads[idx], 'sad': sads_full_path[idx]})
        return sad_ret

    def device_managers(self):
        if self.domMgr_ptr is None:
            raise ResourceNotFound('domain', self.name)
        dev_mgrs = self.domMgr_ptr.devMgrs
        dev_mgrs_dict = []
        for dev_mgr in dev_mgrs:
            dev_mgrs_dict.append({'name': dev_mgr.name, 'id': dev_mgr.id})

        return dev_mgrs_dict

    def devices(self, dev_mgr_id):
        devs = self.find_device(dev_mgr_id)
        ret_dict = []
        for dev in devs:
            ret_dict.append({'name': dev.name, 'id': dev._id})
        return ret_dict

    def services(self, dev_mgr_id):
        svcs = self.find_service(dev_mgr_id)
        ret_dict = []
        for svc in svcs:
            ret_dict.append({'name': svc.name, 'id': svc._id})
        return ret_dict
