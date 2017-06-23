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
from ossie.cf import CF  # For AllocationRequests
from ossie.cf import StandardEvent  # For the EventHelper
from ossie.utils import redhawk
from ossie.events import GenericEventConsumer
import struct
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

class AllocateError(Exception):
    def __init__(self, id='', msg=''):
        self.id = id
        self.msg = msg

    def __str__(self):
        return "Not able to allocate allocation '%s'. %s" % (self.id, self.msg)

class DeallocateError(Exception):
    def __init__(self, id='', msg=''):
        self.id = id
        self.msg = msg

    def __str__(self):
        return "Not able to deallocate allocation '%s'. %s" % (self.id, self.msg)

# Helper class to convert the enumeration fields to something JSON serializable
class EventHelper(object):
    ENUM_MAP = {
        'sourceCategory'      : dict([(str(val), idx) for idx, val in enumerate(StandardEvent.SourceCategoryType._items)]),
        'stateChangeCategory' : dict([(str(val), idx) for idx, val in enumerate(StandardEvent.StateChangeCategoryType._items)]),
        'stateChangeFrom'     : dict([(str(val), idx) for idx, val in enumerate(StandardEvent.StateChangeType._items)]),
        'stateChangeTo'       : dict([(str(val), idx) for idx, val in enumerate(StandardEvent.StateChangeType._items)]),
        }

    @staticmethod
    def format_event(event):
        formattedEvent = {}

        if type(event) == dict:
            for k, v in event.iteritems():
                if k in EventHelper.ENUM_MAP:
                    formattedEvent[k] = {
                        'value'         : str(v),
                        'enumerations'  : EventHelper.ENUM_MAP[k]
                    }
                elif type(v) == list:
                    formattedEvent[k] = []
                    for item in v:
                        formattedEvent[k].append(EventHelper.format_event(item))
                elif k == "sourceIOR":
                    formattedEvent[k] = str(event)
                else:
                    formattedEvent[k] = EventHelper.format_event(v)
        else:
            formattedEvent = event

        return formattedEvent


class TopicConsumer (GenericEventConsumer):
    __registration_id = None

    def __init__(self, domain, on_disconnect=None, filter=None, keep_structs=None):
        GenericEventConsumer.__init__(self, self.deliver, on_disconnect, filter, keep_structs)
        self.__listeners = []
        self.__domain = domain
        self.__registration_id = str(domain + str(uuid.uuid4()))

    @property
    def registration_id(self):
        return self.__registration_id
    

    def deliver(self, event, typecode):
        def attempt(callback, msg):
            try:
                callback(msg)
                return True
            except WebSocketClosedError as e:
                return False

        if type(event) == list:
            for k in event:
                self.deliver(k, typecode)
        else:
            message = EventHelper.format_event(event)
            self.__listeners[:] = [cb for cb in self.__listeners if attempt(cb, message)]


    def add_listener(self, callbackFn):
        if callbackFn not in self.__listeners:
            self.__listeners.append(callbackFn)

    def rm_listener(self, callbackFn):
        self.__listeners[:] = [cb for cb in self.__listeners if callbackFn != cb]


class Domain:
    allocationMgr_ptr = None
    domMgr_ptr = None
    fileMgr_ptr = None
    odmListener = None
    topicHandlers = None
    name = None

    def __init__(self, domainname):
        logging.trace("Establishing domain %s", domainname, exc_info=True)
        self.name = domainname
        self.topicHandlers = {}
        try:
            self._establish_domain()
        except StandardError, e:
            logging.warn("Unable to find domain %s", e, exc_info=1)
            raise ResourceNotFound("domain", domainname)

    def __del__(self):
        if self.domMgr_ptr and self.topicHandlers:
            for k, v in self.topicHandlers.items():
                try: 
                    self.domMgr_ptr.unregisterFromEventChannel(v.registration_id, k)
                except:
                    pass # TODO: Ignore the corba exception, specifically BAD_PARAM

    def disconnect(self):
        old = dict(self.topicHandlers)
        for topic in old:
            self.channel_disconnected(topic)

    def channel_disconnected(self, topic):
        if topic in self.topicHandlers:
            try:
                self.domMgr_ptr.unregisterFromEventChannel(self.topicHandlers[topic].registration_id, topic)
            except:
                pass # TODO: Ignore the corba exception, specifically BAD_PARAM
            del self.topicHandlers[topic]

    def add_event_listener(self, callbackFn, topic):
        if topic not in self.topicHandlers:
            handler = TopicConsumer(self.name, partial(self.channel_disconnected, topic))
            self.domMgr_ptr.registerWithEventChannel(handler._this(), handler.registration_id, str(topic))
            self.topicHandlers[topic] = handler
        self.topicHandlers[topic].add_listener(callbackFn)


    def rm_event_listener(self, callbackFn, topic=None):
        if not topic:
            for k in self.topicHandlers:
                self.rm_event_listener(callbackFn, k)
        else:
            self.topicHandlers[topic].rm_listener(callbackFn);

    def _establish_domain(self):
        redhawk.setTrackApps(False)
        self.domMgr_ptr = redhawk.attach(str(self.name))
        self.allocationMgr_ptr = self.domMgr_ptr.ref._get_allocationMgr()
        self.fileMgr_ptr = self.domMgr_ptr._get_fileMgr()

    def properties(self):
        props = self.domMgr_ptr._properties
        return props

    def event_channels(self, number):
        return self.domMgr_ptr.getEventChannelMgr().listChannels(int(number))[0]

    def get_allocation_info(self):
        if self.allocationMgr_ptr:
            return self.allocationMgr_ptr
        raise ResourceNotFound('allocation manager', self.name)

    def get_domain_info(self):
        if self.domMgr_ptr:
            return self.domMgr_ptr
        raise ResourceNotFound('domain', self.name)

    def get_path(self, path):
        fileInfos = self.fileMgr_ptr.list(path)

        contents = ''
        directories = []
        files = []

        # Iterate over the files at this path
        for fileInfoType in fileInfos:
            executable = False
            readOnly = True

            for fileProp in fileInfoType.fileProperties:
                if fileProp.id == 'READ_ONLY':
                    readOnly = fileProp.value.value()
                elif fileProp.id == 'EXECUTABLE':
                    executable = fileProp.value.value()

            newObject = {
                'executable': executable,
                'name': str(fileInfoType.name), 
                'read_only': readOnly,
                'size': fileInfoType.size
            }

            if str(fileInfoType.kind) == 'DIRECTORY':
                directories.append(newObject)
            elif str(fileInfoType.kind) == 'PLAIN':
                files.append(newObject)

        # No need to read the file if there are directories
        if len(directories) != 0:
            return {'contents': contents, 'directories': directories, 'files': files}

        # No need to read the file if there are multiple files
        if len(files) != 1:
            return {'contents': contents, 'directories': directories, 'files': files}

        # Don't return the contents of the file if this is a directory path
        if path.endswith('/'):
            return {'contents': contents, 'directories': directories, 'files': files}

        # Read the file to the user
        fileToRead = self.fileMgr_ptr.open(path, True)

        contents = fileToRead.read(fileToRead.sizeOf())

        if not path.endswith(('.py', '.m', '.xml')):
            contents = struct.unpack(str(fileToRead.sizeOf()) + 'B', contents)

        fileToRead.close()

        return {'contents': str(contents), 'directories': directories, 'files': files}

    def find_allocation(self, allocation_id=None):
        _allocationMgr = self.get_allocation_info()
        allocations = _allocationMgr.localAllocations([])

        if not allocation_id:
            return allocations

        for allocation in allocations:
            if allocation.allocationID == allocation_id:
                return allocation
        raise ResourceNotFound('allocation', allocation_id)

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

    def allocate(self, allocation_id, device_ids, properties, source_id):
        _dom = self.get_domain_info()
        allocationMgr = self.get_allocation_info()
        
        if not device_ids or len(device_ids) == 0:
            device_ids = [device._id for device in _dom.devices]
        
        device_refs = [device.ref for device in _dom.devices]
        allocationRequest = CF.AllocationManager.AllocationRequestType(str(allocation_id), properties, device_ids, device_refs, str(source_id))

        try:
            allocationMgr.allocate([allocationRequest])
            return allocation_id
        except Exception, e:
            raise AllocateError(allocation_id, str(e))

    def allocations(self):
        allocations_dict = []
        allocations = self.find_allocation()
        for allocation in allocations:
            allocations_dict.append({'id': allocation.allocationID, 'deviceId': allocation.allocatedDevice._get_identifier()})
        return allocations_dict

    def append(self, path, contents):
        if not self.fileMgr_ptr.exists(path):
            return {'status': 'failure', 'message': 'file does not exist'}

        fileToAppend = self.fileMgr_ptr.open(path, False)

        fileToAppend.setFilePointer(fileToAppend.sizeOf())

        fileToAppend.write(contents)

        fileToAppend.close()

        return {'status': 'success'}

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

    def create(self, path, contents, read_only):
        if self.fileMgr_ptr.exists(path):
            return {'status': 'failure', 'message': 'file already exists'}

        fileType = 'DIRECTORY'

        if not path.endswith('/'):
            fileType = 'FILE'

        if contents or fileType == 'FILE':
            newFile = self.fileMgr_ptr.create(path)
        else:
            self.fileMgr_ptr.mkdir(path)
            return {'status': 'success'}

        if contents:
            if type(contents) == list:
                contents = struct.pack(str(len(contents)) + 'B', *contents)

            newFile.write(contents)

        newFile.close()

        return {'status': 'success'}

    def deallocate(self, allocation_ids):
        allocationMgr = self.get_allocation_info()
        try:
            allocationMgr.deallocate([str(allocation_id) for allocation_id in allocation_ids])
            return allocation_ids
        except Exception, e:
            raise DeallocateError(allocation_ids, str(e))

    def launch(self, app_name):
        _dom = self.get_domain_info()
        try:
            app = _dom.createApplication(app_name)
            return app._get_identifier()
        except Exception, e:
            raise WaveformLaunchError(app_name, str(e))

    def move(self, from_path, to_path, keep_original):
        if not self.fileMgr_ptr.exists(from_path):
            return {'status': 'failure', 'message': 'from path does not exist'}

        if keep_original:
            self.fileMgr_ptr.copy(from_path, to_path)
            return {'status': 'success'}
        else:
            self.fileMgr_ptr.move(from_path, to_path)
            return {'status': 'success'}

    def release(self, app_id):
        app = self.find_app(app_id)
        try:
            app.releaseObject()
            return app_id
        except Exception, e:
            raise ApplicationReleaseError(app_id, str(e))

    def remove(self, path):
        if not self.fileMgr_ptr.exists(path):
            return {'status': 'failure', 'message': 'file does not exist'}

        fileType = 'DIRECTORY'

        if not path.endswith('/'):
            fileType = 'FILE'

        if fileType == 'FILE':
            self.fileMgr_ptr.remove(path)
        else:
            self.fileMgr_ptr.rmdir(path)

        return {'status': 'success'}

    def replace(self, path, contents):
        if not self.fileMgr_ptr.exists(path):
            return {'status': 'failure', 'message': 'file does not exist'}

        self.fileMgr_ptr.remove(path)

        fileToCreate = self.fileMgr_ptr.create(path)

        fileToCreate.write(contents)

        fileToCreate.close()

        return {'status': 'success'}

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