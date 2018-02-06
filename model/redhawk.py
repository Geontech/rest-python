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
    redhawk.py

    Asynchronous Tornado service for REDHAWK. Maps the functions
    in domain.py and caches the domain object.
"""
from _utils.tasking import background_task

from domain import Domain, scan_domains, ResourceNotFound

from ossie.cf import CF
from ossie.properties import __TYPE_MAP as TYPE_MAP
from ossie.properties import props_from_dict, props_to_dict

from tornado.websocket import WebSocketClosedError
from tornado import ioloop, log

import collections
import copy

class Redhawk(object):
    __domains = None
    statusListeners = None
    
    def __init__(self):
        self.__domains = {}
        self.statusListeners = []
        self.pollTimer = ioloop.PeriodicCallback(self.poll_domains, 5000)
        self.pollTimer.start()

    def _get_domain(self, domain_name):
        name = str(domain_name)
        if not name in self.__domains:
            self.__domains[name] = Domain(domain_name)
        
        return self.__domains[name]

    def _status_message(self):
        return {'domains': self.__domains.keys() }

    def poll_domains(self):
        domainIdsNow = scan_domains()
        additions = [ domainId for domainId in domainIdsNow          if domainId not in self.__domains.keys() ]
        removals =  [ domainId for domainId in self.__domains.keys() if domainId not in domainIdsNow ]
        for a in additions:
            self.__domains[a] = self._get_domain(a)
        for r in removals:
            self.__domains[r].disconnect()
            del self.__domains[r]

        def _attemptCallback(fn, msg):
            try:
                fn(msg)
                return True
            except WebSocketClosedError:
                return False

        if additions or removals:
            message = self._status_message()
            message.update(dict(added=additions, removed=removals))
            self.statusListeners[:] = [h for h in self.statusListeners if _attemptCallback(h, message)]

    def add_redhawk_listener(self, callbackFn):
        self.statusListeners.append(callbackFn)
        callbackFn(self._status_message())

    def rm_redhawk_listener(self, callbackFn):
        self.statusListeners.remove(callbackFn)

    def add_event_listener(self, callbackFn, domain_name=None, topic=None):
        if domain_name in self.__domains:
            self.__domains[domain_name].add_event_listener(callbackFn, topic)

    def rm_event_listener(self, callbackFn, domain_name=None, topic=None):
        if domain_name in self.__domains:
            self.__domains[domain_name].rm_event_listener(callbackFn, topic)


    @background_task
    def get_all_event_channels(self, number):
        eventChannels = []
        for i in self.__domains.values():
            eventChannels.extend(i.event_channels(number))
        eventChannelNames = []
        for i in eventChannels:
            eventChannelNames.append(i.channel_name)
        return eventChannelNames



            
    ##############################
    # DOMAIN

    @background_task
    def get_domain_list(self):
        return scan_domains()

    @background_task
    def get_domain_info(self, domain_name):
        dom = self._get_domain(domain_name)
        return dom.get_domain_info()

    @background_task
    def get_domain_properties(self, domain_name):
        dom = self._get_domain(domain_name)
        return dom.properties()

    @background_task
    def get_domain_event_channels(self, domain_name):
        dom = self._get_domain(domain_name)
        eventChannels = dom.event_channels(150)
        eventChannelNames = []
        for i in eventChannels:
            eventChannelNames.append(i.channel_name)
        return eventChannelNames

    ##############################
    # ALLOCATION

    @background_task
    def allocate(self, domain_name, allocation_id, device_ids, properties, source_id):
        dom = self._get_domain(domain_name)
        props = props_from_dict(Redhawk._clean_property(properties))
        return dom.allocate(allocation_id, device_ids, props, source_id)

    @background_task
    def get_allocation(self, domain_name, allocation_id):
        dom = self._get_domain(domain_name)
        return dom.find_allocation(allocation_id)

    @background_task
    def get_allocation_list(self, domain_name):
        dom = self._get_domain(domain_name)
        return dom.allocations()

    @background_task
    def deallocate(self, domain_name, allocation_ids):
        dom = self._get_domain(domain_name)
        return dom.deallocate(allocation_ids)

    ##############################
    # APPLICATION

    @background_task
    def get_application(self, domain_name, app_id):
        dom = self._get_domain(domain_name)
        return dom.find_app(app_id)

    def _get_application(self, domain_name, app_id):
        dom = self._get_domain(domain_name)
        return dom.find_app(app_id)

    @background_task
    def get_application_list(self, domain_name):
        dom = self._get_domain(domain_name)
        return dom.apps()

    @background_task
    def get_available_applications(self, domain_name):
        dom = self._get_domain(domain_name)
        return dom.available_apps()

    @background_task
    def launch_application(self, domain_name, app_name):
        dom = self._get_domain(domain_name)
        return dom.launch(app_name)

    @background_task
    def release_application(self, domain_name, app_id):
        dom = self._get_domain(domain_name)
        return dom.release(app_id)

    @background_task
    def application_configure(self, domain_name, app_id, new_properties):
        app = self._get_application(domain_name, app_id)
        props = Redhawk._application_externalProps(app)
        changes = Redhawk._get_prop_changes(props, new_properties)
        return app.configure(changes)

    '''
    Helper function to streamline getting a property list similar to what one
    gets from components, devices, etc.  This can duplicate external properties
    listed by the assembly controller in the event the user wants to make some
    external under a namespaced ID.
    '''
    @staticmethod
    def _application_externalProps(app):
        props = app._getPropertySet()
        for epid, t in app._externalProps.iteritems():
            pid = t[0] # First item is the property id relative to the component
            cid = t[1] # Second item in tuple is prefix of component identifier
            log.app_log.debug('Looking for {}: {}'.format(cid, pid))
            for comp in app.comps:
                if comp.identifier.split(':')[0] == cid:
                    log.app_log.debug('Found component')
                    for prop in comp._properties:
                        log.app_log.debug('Checking {} == {}'.format(prop.id, pid))
                        if prop.id == pid:
                            eprop = copy.copy(prop)
                            eprop.id = epid;
                            props.append(eprop)
                            log.app_log.debug('Found external property {} -> {}'.format(epid, pid))
                            break;
                    break;
        log.app_log.debug('All properties: {}'.format(props))
        return props

    ##############################
    # COMMON PROPERTIES
    '''
    Cleans out IDs being unicode, etc. since CF can't handle unicode strings.
    '''
    @staticmethod
    def _clean_property(property):
        if isinstance(property, basestring):
            return str(property)
        elif isinstance(property, collections.Mapping):
            return dict(map(Redhawk._clean_property, property.iteritems()))
        elif isinstance(property, collections.Iterable):
            return type(property)(map(Redhawk._clean_property, property))
        else:
            return property

    @staticmethod
    # CF.Properties and dict() of { 'id': value, ... }
    # Use force to treat all ID matches as required changes
    def _get_prop_changes(current_props, new_properties, force=False):
        changes = []
        for prop in current_props:
            if prop.id in new_properties:
                if new_properties[prop.id] != prop.queryValue() or force:
                    changes.append(
                        CF.DataType(
                            prop.id,
                            prop.toAny(
                                    Redhawk._clean_property(new_properties[prop.id])
                                )
                            )
                        )
        log.app_log.debug('Current properties: {}'.format(current_props))
        log.app_log.debug('New properties:     {}'.format(new_properties))
        log.app_log.debug('Changes:            {}'.format(changes))
        return changes

    ##############################
    # COMPONENT

    @background_task
    def get_component(self, domain_name, app_id, comp_id):
        dom = self._get_domain(domain_name)
        return dom.find_component(app_id, comp_id)

    def _get_component(self, domain_name, app_id, comp_id):
        dom = self._get_domain(domain_name)
        return dom.find_component(app_id, comp_id)

    @background_task
    def get_component_list(self, domain_name, app_id):
        dom = self._get_domain(domain_name)
        return dom.components(app_id)

    @background_task
    def component_configure(self, domain_name, app_id, comp_id, new_properties):
        comp = self._get_component(domain_name, app_id, comp_id)
        changes = Redhawk._get_prop_changes(comp._properties, new_properties)
        return comp.configure(changes)

    ##############################
    # DEVICE MANAGER

    @background_task
    def get_device_manager(self, domain_name, device_manager_id):
        dom = self._get_domain(domain_name)
        return dom.find_device_manager(device_manager_id)

    @background_task
    def get_device_manager_list(self, domain_name):
        dom = self._get_domain(domain_name)
        return dom.device_managers()

    ##############################
    # DEVICE

    @background_task
    def get_device_list(self, domain_name, device_manager_id):
        dom = self._get_domain(domain_name)
        return dom.devices(device_manager_id)

    @background_task
    def get_device(self, domain_name, device_manager_id, device_id):
        dom = self._get_domain(domain_name)
        return dom.find_device(device_manager_id, device_id)

    def _get_device(self, domain_name, device_manager_id, device_id):
        dom = self._get_domain(domain_name)
        return dom.find_device(device_manager_id, device_id)

    @background_task
    def device_configure(self, domain_name, device_manager_id, device_id, new_properties):
        dev = self._get_device(domain_name, device_manager_id, device_id)
        changes = Redhawk._get_prop_changes(dev._properties, new_properties)
        try:
            return dev.configure(changes), ''
        except Exception as e:
            return False, "{0}".format(e);


    @background_task
    def device_allocate(self, domain_name, device_manager_id, device_id, new_properties):
        dev = self._get_device(domain_name, device_manager_id, device_id)
        changes = Redhawk._get_prop_changes(dev._properties, new_properties, True)
        try:
            return dev.allocateCapacity(changes), ''
        except Exception as e:
            return False, "{0}".format(e);

    @background_task
    def device_deallocate(self, domain_name, device_manager_id, device_id, new_properties):
        dev = self._get_device(domain_name, device_manager_id, device_id)
        changes = Redhawk._get_prop_changes(dev._properties, new_properties, True)
        try:
            dev.deallocateCapacity(changes)
            return True, ''
        except Exception as e:
            return False, "{0}".format(e);

    ##############################
    # FILESYSTEM

    @background_task
    def append(self, domain_name, path, contents):
        dom = self._get_domain(domain_name)
        return dom.append(path, contents)
    
    @background_task
    def create(self, domain_name, path, contents, read_only):
        dom = self._get_domain(domain_name)
        return dom.create(path, contents, read_only)

    @background_task
    def get_path(self, domain_name, path):
        dom = self._get_domain(domain_name)
        pathObject = dom.get_path(path)
        return pathObject

    @background_task
    def move(self, domain_name, from_path, to_path, keep_original):
        dom = self._get_domain(domain_name)
        return dom.move(from_path, to_path, keep_original)

    @background_task
    def remove(self, domain_name, path):
        dom = self._get_domain(domain_name)
        return dom.remove(path)

    @background_task
    def replace(self, domain_name, path, contents):
        dom = self._get_domain(domain_name)
        return dom.replace(path, contents)

    ##############################
    # SERVICE

    @background_task
    def get_service_list(self, domain_name, device_manager_id):
        dom = self._get_domain(domain_name)
        return dom.services(device_manager_id)
    
    ##############################
    # GENERIC
    
    @background_task
    def get_object_by_path(self, path, path_type):
        '''
            Locates a redhawk object with the given path, and path type. 
            Returns the object + remaining path:

               comp, opath = locate(ipath, 'component')


            Valid path types are:
                'application' - [ domain id, application-id ]
                'component' - [ domain id, application-id, component-id ]
                'device-mgr' - [ domain id, device-manager-id ]
                'device' - [ domain id, device-manager-id, device-id ]
        '''
        domain = self._get_domain(path[0])
        if path_type == 'application':
            return domain.find_app(path[1]), path[2:]
        elif path_type == 'component':
            return domain.find_component(path[1], path[2]), path[3:]
        elif path_type == 'device-mgr':
            return domain.find_device_manager(path[1]), path[2:]
        elif path_type == 'device':
            return domain.find_device(path[1], path[2]), path[3:]
        raise ValueError("Bad path type %s.  Must be one of application, component, device-mgr or device" % path_type)

