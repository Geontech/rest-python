/*
 * This file is protected by Copyright. Please refer to the COPYRIGHT file
 * distributed with this source distribution.
 *
 * This file is part of REDHAWK admin-console.
 *
 * REDHAWK admin-console is free software: you can redistribute it and/or modify it
 * under the terms of the GNU Lesser General Public License as published by the
 * Free Software Foundation, either version 3 of the License, or (at your
 * option) any later version.
 *
 * REDHAWK admin-console is distributed in the hope that it will be useful, but WITHOUT
 * ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
 * FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License
 * for more details.
 *
 * You should have received a copy of the GNU Lesser General Public License
 * along with this program.  If not, see http://www.gnu.org/licenses/.
 */
angular.module('RedhawkServices', ['SubscriptionSocketService', 'RedhawkNotifications', 'RedhawkConfig', 'RedhawkREST'])
  .config(['$httpProvider', function($httpProvider) {
    $httpProvider.defaults.transformResponse.unshift(function(response, headersGetter) {
      var ctype = headersGetter('content-type');
      if(ctype && ctype.indexOf('json') > -1) {
        var reg = /:\s?(Infinity|-Infinity|NaN)\s?\,/g;
        return response.replace(reg, ": \"$1\", ");
      } else {
        return response;
      }
    });
  }])
  .constant('BuiltInFactoryNames', {
    DOMAIN:         'RedhawkDomain',
    DEVICEMANAGER:  'RedhawkDeviceManager',
    DEVICE:         'RedhawkDevice',
    FEIDEVICE:      'RedhawkFeiDevice',
    FEITUNERDEVICE: 'RedhawkFeiTunerDevice',
    WAVEFORM:       'RedhawkWaveform',
    COMPONENT:      'RedhawkComponent',
  })
  /* Singleton REDHAWK Service for returning Domain factories */
  .service('Redhawk', ['$injector', 'RedhawkREST', 'BuiltInFactoryNames',
    function($injector, RedhawkREST, BuiltInFactoryNames){
      /**
       *
       * Factory Object returned to the injector. Used to store {Domain} objects.
       *
       * Public Interfaces:
       * {getDomainIds()}
       * {getDomain()}
       *
       * @type {{
       *          getDomainIds: function(),
       *          getDomain: function(),
       *          addDomain: function()
       *       }}
       */
      var redhawk = this;  // This conflict below...
      redhawk.domainIds = null;
      redhawk.__domains = {};
      /**
       *  Returns a list of REDHAWK Domains available.
       *
       * @returns {Array.<string>}
       */
      redhawk.getDomainIds = function(){
        if(!redhawk.domainIds) {
          redhawk.domainIds = [];

          redhawk.domainIds.$promise = RedhawkREST.domain.query().$promise.then(function(data){
            var domains = data['domains'];
            angular.forEach(domains, function(info) {
              this.push(info);
            }, redhawk.domainIds);
            return redhawk.domainIds;
          });
        }

        return redhawk.domainIds;
      };

      /**
       * Returns a resource with a promise to a {Domain} object.
       *
       * @param id - String ID of the domain
       * @param factoryName - String name to inject as the constructor rather than RedhawkDomain
       * @returns {Domain}
       */
      redhawk.getDomain = function(id, factoryName){
        var storeId = id + ((factoryName) ? factoryName : BuiltInFactoryNames.DOMAIN);

        if(!redhawk.__domains[storeId]) {
          var constructor = (factoryName) ? $injector.get(factoryName) : $injector.get(BuiltInFactoryNames.DOMAIN);
          redhawk.__domains[storeId] = new constructor(id);
        }

        return redhawk.__domains[storeId];
      };

      // FIXME: Whatever JSON someone was expecting to receive, they did not implement the push
      // back at the server in the rest-python release.  TG 2/2014 added an alternate 
      // status implementation and retained this block (commented) in the event a future release
      // restores the appropriate server-side interface.
      /*
      RedhawkSocket.status.addJSONListener(function(event) {
        var element = event.ChangedElement;
        var elementType = element.eobj_type;

        var domain = redhawk.__domains[event.domain];
        if(!domain) {
          if(event.domain)
            console.log("Skipping notification for other domain '"+event.domain+"'.");
          return;
        }

        switch(elementType) {
          case "ScaWaveformFactory":
            if(redhawk.domain)
              domain._reload();
            break;
          case "ScaWaveform":
            var applicationId = event.waveformInstance;
            if(domain.waveforms[applicationId]){
              //console.log("Updating Waveform  "+applicationId);
              domain.waveforms[applicationId]._update(element);
            }
            break;
          case "ScaComponent":
            var compId = uniqueId(event.componentInstance, event.waveformInstance);
            if(domain.components[compId]) {
              //console.log("Updating Component "+compId);
              domain.components[compId]._update(element);
            }
            break;
          case "ScaSimpleProperty":
            var path = event.Notification.path;
            updateProperties(path, element);
            break;
          default:
            //console.log("RedhawkDomain::NOTIF ["+elementType+"] Unknown type");
            //console.log(event);
        }
      });
      */
      /**
       * Recursively searches the properties array looking for the property with the given id.
       * @param properties {Array} - Array of property objects
       * @param propertyId {string} - Id of the property to find
       * @returns {Object} - property with the given id
       */
      var findPropertyByDCE = function(properties, propertyId){
        var res = undefined;

        angular.forEach(properties, function(prop){
          if(prop.id==propertyId) {
            res = prop;
          } else if(prop.structs) {
            res = findPropertyByDCE(prop.structs, propertyId);
          }
        });

        return res;
      };

      /**
       * Modifies a property in an array of properties based on the propertyId.
       * @param properties {Array} - Array of nested properties
       * @param propertyId {string} - The DCE of the property
       * @param newProp {Object} - New contents of the property
       */
      var updateProperty = function(properties, propertyId, newProp) {
        var prop = findPropertyByDCE(properties, propertyId);

        if(prop) {
          if(prop.name == newProp.name) {
            //console.log("RedhawkDomain::updateProperty - Found property '"+prop.name+"'.");
            angular.extend(prop, newProp);
          }

          angular.forEach(prop.simples, function(simple){
            if(simple.id==newProp.id) {
              //console.log("RedhawkDomain::updateProperty - Found simple '"+simple.name+"'.");
              angular.extend(simple, newProp);
            }
          });
        }
      };

      /**
       * Searches all the cached domain objects and updates new property based on the path.
       * @param {string} path - String representing the property location, modeled after the rest API URI
       * @param {object} newProperty - New property value.
       */
      var updateProperties = function(path, newProperty){
        var nav = path.split('/');

        // Path follows the format of /domains/{domainId}/{typeName}/{typeId}/{type2Name}/{type2Id}/..
        var domainId = nav[2];
        var type = nav[3];
        var typeId = nav[4];
        var subType = nav[5];
        var subTypeId = nav[6];

        var domain = this.__domains[domainId];
        if(!domain) {
          return;
        }

        // Eventually type should end with /properties/{propertyId}
        var propertyId = nav[nav.indexOf('properties')+1];
        if(propertyId == 0) {
          console.log("RedhawkDomain::updateProperties::WARNING - Cannot find propertiesId");
          console.log(nav);
        }

        var properties;
        if(type=='properties') {
          properties = domain.properties;
        } else if(type=='waveforms' && subType=='properties') {
          var waveform = domain.waveforms[typeId];
          if(waveform) {
            properties = waveform.properties;
          }
        } else if(type=='waveforms' && subType == 'components') {
          var id = uniqueId(subTypeId, typeId);
          var component = domain.components[id];
          if(component){
            properties = component.properties;
          }
        } else if(type=='deviceManagers' && subType=='properties') {
          var deviceManager = domain.deviceManagers[typeId];
          if(deviceManager) {
            properties = deviceManager.properties;
          }
        } else if(type=='deviceManagers' && subType=='devices') {
          var device = domain.devices[subTypeId];
          if(device){
            properties = device.properties
          }
        } else {
          console.log("RedhawkDomain::updateProperties - Unknown Properties Container - "+path);
        }

        if(!properties) {
          return;
        }

        // properties all follow the same format so they can
        // be passed to a generalized function.
        updateProperty(properties, propertyId, newProperty);
      };
  }])

  /**
   * Creates a listener to all event channels and stores the messages.
   *
   * @constructor
   */
  .factory('RedhawkEventChannel', ['RedhawkSocket',
    function(RedhawkSocket) {
      return function(domain, parent_on_msg, parent_on_connect) {
        var self = this;

        self.messages = [];
        self.channels = [];
        var on_connect = function(){
          domain.getEventChannels().$promise.then(function(result) {
            angular.forEach(result.eventChannels, function(chan) {
              self.addChannel(chan);
            });
            if (parent_on_connect)
              parent_on_connect(self);
          });
        };

        var on_msg = function(json){
          self.messages.push(json);

          if(self.messages.length > 500)
            angular.copy(self.messages.slice(-500), self.messages);

          if (parent_on_msg)
            parent_on_msg.call(domain, json);
        };
        var eventMessageSocket = RedhawkSocket.eventChannel(on_msg, on_connect);
        eventMessageSocket.socket.addBinaryListener(function(data){
          console.log("WARNING Event Channel Binary Data!");
        });

        self.addChannel = function(channel) {
          if (-1 == self.channels.indexOf(channel)) {
            eventMessageSocket.addChannel(channel, domain._restId);
            self.channels.push(channel);
          }
        }

        self.removeChannel = function(channel) {
          var chanIdx = self.channels.indexOf(channel)
          if (-1 < chanIdx) {
            eventMessageSocket.removeChannel(channel, domain._restId);
            self.channels.splice(chanIdx, 1);
          }
        }

        self.getMessages = function() {
          return self.messages;
        };
        self.getChannelNames = function() {
          return self.channels;
        };
      };
  }])

  /** 
   * Angular-style resource that encapsulates the Domain interface from the server.
   *
   * @param id - {string} Domain name
   * @constructor
   */
  .factory('RedhawkDomain', 
           ['$injector', 'RedhawkNotificationService', 'RedhawkREST', 'RedhawkDeviceManager', 'RedhawkDevice', 'RedhawkWaveform', 'RedhawkComponent', 'RedhawkEventChannel', 'BuiltInFactoryNames',
    function($injector,   RedhawkNotificationService,   RedhawkREST,   RedhawkDeviceManager,   RedhawkDevice,   RedhawkWaveform,   RedhawkComponent,   RedhawkEventChannel, BuiltInFactoryNames) {
      var RedhawkDomain = function(id) {
        var self = this;
        var notify = RedhawkNotificationService;

        self.getEvents = function() {
          return self.events;
        }

        /**
         * Update the data in this object (used for both REST and socket-based updates).
         * @param updateData
         * @private
         */
        self._update = function(updateData) {
          if(updateData) {
            angular.extend(self, updateData);
            self._updateFinished();
          }
        };

        /**
         * Handles loading data from the REST interface.
         * @param id
         * @private
         */
        self._load = function(id) {
          self._restId = id;

          if (!self.events)
            self.events = new RedhawkEventChannel(self, self.on_msg, self.on_connect);
          self.deviceManagers = {};
          self.waveforms = {};
          self.components = {};
          self.devices = {};

          self.$promise = RedhawkREST.domain.info({domainId: self._restId}, function(data) {
            self._update(data);
          }).$promise;
        };

        /**
         * Reloads the data based on existing identifiers.
         * @private
         */
        self._reload = function() { self._load(self._restId); };

        /**
         * Configure REDHAWK properties for this object.
         * @param properties
         */
        self.configure = function(properties) {
          RedhawkREST.domain.configure({domainId: self._restId},{properties: properties});
        };

        /**
         * Gets filesystem information at path.
         * @deprecated - Not implemented in current versions of the backend
         * @param path
         * @returns {*}
         */
        self.getFileSystem = function(path) {
          return RedhawkREST.fileSystem.query({domainId: self._restId, path: path});
        };

        /**
         * Get event channels available.
         * @deprecated - Not implemented in current versions of the backend
         * @returns {*}
         */
        self.getEventChannels = function() {
          return RedhawkREST.domain.events({domainId: self._restId});
        };

        /**
         * Get a device object from this domain.
         * @param id
         * @param deviceManagerId
         * @param factoryName
         * @returns {*}
         */
        self.getDevice = function(id, deviceManagerId, factoryName) {
          var storeId = id + ((factoryName) ? factoryName : BuiltInFactoryNames.DEVICE);
          if(!self.devices[storeId]){
            var constructor = (factoryName) ? $injector.get(factoryName) : RedhawkDevice;
            self.devices[storeId] = new constructor(id, self._restId, deviceManagerId);
          }

          return self.devices[storeId];
        };

        /**
         * Get a device manager object from this domain.
         * @param id
         * @param factoryName
         * @returns {*}
         */
        self.getDeviceManager = function(id, factoryName) {
          var storeId = id + ((factoryName) ? factoryName : BuiltInFactoryNames.DEVICEMANAGER);
          if(!self.deviceManagers[storeId]) {
            var constructor = (factoryName) ? $injector.get(factoryName) : RedhawkDeviceManager;
            self.deviceManagers[storeId] = new constructor(id, self._restId);
          }
          return self.deviceManagers[storeId];
        };
        
        /**
         * Get a component object from this domain.
         * @param id
         * @param applicationId
         * @param factoryName
         * @returns {*}
         */
        self.getComponent = function(id, applicationId, factoryName) {
          var storeId = id + ((factoryName) ? factoryName : BuiltInFactoryNames.COMPONENT);
          if(!self.components[storeId]) {
            var constructor = (factoryName) ? $injector.get(factoryName) : RedhawkComponent;
            self.components[storeId] = new constructor(id, self._restId, applicationId);
          }

          return self.components[storeId];
        };

        /**
         * Get a waveform object from this domain.
         * @param id
         * @param factoryName
         * @returns {*}
         */
        self.getWaveform = function(id, factoryName){
          var storeId = id + ((factoryName) ? factoryName : BuiltInFactoryNames.WAVEFORM);
          if(!self.waveforms[storeId]) {
            var constructor = (factoryName) ? $injector.get(factoryName) : RedhawkWaveform;
            self.waveforms[storeId] = new constructor(id, self._restId);
          }

          return self.waveforms[storeId];
        };

        /**
         * Get a list of Waveforms available for launching.
         * @returns {Array}
         */
        self.getLaunchableWaveforms = function() {
          if(!self.availableWaveforms) {
            self.availableWaveforms = [];
            self.availableWaveforms.$promise =
                RedhawkREST.waveform.status({domainId: self._restId}).$promise.then(function(data){
                  angular.forEach(data['waveforms'], function(item){
                    this.push(item['name']);
                  },self.availableWaveforms);

                  return self.availableWaveforms;
                }
            );
          }

          return self.availableWaveforms
        };

        /**
         * Launch a Waveform.
         * @param name
         * @returns {*}
         */
        self.launch = function(name) {
          return RedhawkREST.waveform.launch({domainId: self._restId}, {name: name},
            function(data){
              notify.success("Waveform "+data['launched']+" launched");
              self._reload();
            },
            function(){
              notify.error("Waveform "+name+" failed to launch.");
            }
          );
        };

        self._load(id);
      };

      // ExternalAPI Methods for extended factories
      RedhawkDomain.prototype._updateFinished = function () { };
      RedhawkDomain.prototype.on_connect = undefined;
      RedhawkDomain.prototype.on_msg = undefined;
      return RedhawkDomain;
  }])
  
  /**
   * Angular-style resource that encapsulates the Waveform interface from the server.
   *
   * @param id
   * @param domainId
   * @constructor
   */
  .factory('RedhawkWaveform', ['Redhawk', 'RedhawkREST', 'RedhawkNotificationService',
    function(Redhawk, RedhawkREST, RedhawkNotificationService) {
      var RedhawkWaveform = function(id, domainId) {
        var self = this;
        var notify = RedhawkNotificationService;

        /**
         * @see {Domain._update()}
         */
        self._update = function(updateData) {
          if(updateData) {
            angular.extend(self, updateData);
            UtilityFunctions.processPorts(self.ports);
            self._updateFinished();
          }
        };

        /**
         * @see {Domain._load()}
         */
        self._load = function(id, domainId) {
          self.$promise = RedhawkREST.waveform.query({applicationId: id, domainId: domainId}, function(data){
            self.domainId = domainId;
            self._update(data);
          }).$promise;
        };
        /**
         * @see {Domain._reload()}
         */
        self._reload = function() {
          self._load(self.id, self.domainId);
        };

        /**
         * Start the Waveform
         * @returns {*}
         */
        self.start = function() {
          return RedhawkREST.waveform.update(
            {applicationId: self.id, domainId: domainId}, {started: true},
            function(){
              notify.success("Waveform "+self.name+" started.");
              self._reload();
            },
            function(){notify.error("Waveform "+self.name+" failed to start.")}
          );
        };
        /**
         * Stop the Waveform
         * @returns {*}
         */
        self.stop = function() {
          return RedhawkREST.waveform.update(
            {applicationId: self.id, domainId: domainId},{started: false},
            function(){
              notify.success("Waveform "+self.name+" stopped.");
              self._reload();
            },
            function(){notify.error("Waveform "+self.name+" failed to stop.");}
          );
        };
        /**
         * Release (delete) the Waveform
         * @returns {*}
         */
        self.release = function() {
          return RedhawkREST.waveform.release(
            {applicationId: self.id, domainId: self.domainId},{},
            function(){
              notify.success("Waveform "+self.name+" released.");
              Redhawk.getDomain(self.domainId)._reload();
            },
            function(){notify.error("Waveform "+self.name+" failed to release.");
          });
        };
        /**
         * @see {Domain.configure()}
         */
        self.configure = function(properties) {
          return RedhawkREST.waveform.configure({applicationId: self.id, domainId: self.domainId}, {properties: properties});
        };

        self._load(id, domainId);
      };

      // ExternalAPI Method for extended factories
      RedhawkWaveform.prototype._updateFinished = function () { };
      return RedhawkWaveform;
    }
  ])

  /**
   * Angular-style resource that encapsulates the Component interface from the server.
   *
   * @param id
   * @param domainId
   * @param applicationId
   * @constructor
   */
  .factory('RedhawkComponent', ['RedhawkREST', '$timeout',
    function (RedhawkREST, $timeout) {
      var RedhawkComponent = function(id, domainId, applicationId) {
        var self = this;

        /**
         * @see {Domain._update()}
         */
        self._update = function(updateData) {
          if(updateData) {
            angular.extend(self, updateData);
            UtilityFunctions.processPorts(self.ports);
            self._updateFinished();
          }
        };

        /**
         * @see {Domain._load()}
         */
        self._load = function(id, domainId, applicationId) {
          self.$promise = RedhawkREST.component.query({componentId: id, applicationId: applicationId, domainId: domainId}, function(data){
            self.waveform = {id: applicationId};
            self.domainId = domainId;
            self._update(data);
          }).$promise;
        };
        /**
         * @see {Domain._reload()}
         */
        self._reload = function() { self._load(self.id, self.domainId, self.waveform.id); };

        /**
         * @see {Domain.configure()}
         */
        self.configure = function(properties) {
          return RedhawkREST.component.configure(
              {componentId: self.id, applicationId: self.waveform.id, domainId: self.domainId},
              {properties: properties},
              function(){ $timeout(self._reload, 1000); }
          );
        };

        self._load(id, domainId, applicationId);
      };

      // External API Method for extended factories
      RedhawkComponent.prototype._updateFinished = function () { };
      return RedhawkComponent;
  }])  
  

  /**
   * Angular-style resource that encapsulates the Device Manager interface from the server.
   * @param id
   * @param domainId
   * @constructor
   */
  .factory('RedhawkDeviceManager', ['RedhawkREST',
    function (RedhawkREST) {
      var RedhawkDeviceManager = function(id, domainId) {
        var self = this;
        /**
         * @see {Domain._update()}
         */
        self._update = function(updateData) {
          if(updateData) {
            angular.extend(self, updateData);
            self._updateFinished();
          }
        };

        /**
         * @see {Domain._load()}
         */
        self._load = function(id, domainId) {
          self.$promise = RedhawkREST.deviceManager.query({managerId: id, domainId: domainId}, function(data){
            self.domainId = domainId;
            self._update(data);
          }).$promise;
        };
        /**
         * @see {Domain._reload()}
         */
        self._reload = function() { self._load(self.id, self.domainId); };

        self._load(id, domainId);
      };

      // External API Method for extended factories
      RedhawkDeviceManager.prototype._updateFinished = function () { };
      return RedhawkDeviceManager;
  }])
  
  /**
   * Angular-style resource that encapsulates the Device interface from the server.
   *
   * @param id
   * @param domainId
   * @param managerId
   * @constructor
   */
  .factory('RedhawkDevice', ['RedhawkREST', '$timeout',
    function (RedhawkREST, $timeout) {
      var RedhawkDevice = function(id, domainId, managerId) {
        var self = this;

        /**
         * @see {Domain._update()}
         */
        self._update = function(updateData) {
          if(updateData) {
            angular.extend(self, updateData);
            UtilityFunctions.processPorts(self.ports);
            self._updateFinished();
          }
        };

        /**
         * @see {Domain._load()}
         */
        self._load = function(id, domainId, managerId) {
          self.$promise = RedhawkREST.device.query({deviceId: id, managerId: managerId, domainId: domainId}, 
            function(data){
              self.deviceManager = {id: managerId};
              self.domainId = domainId;
              self._update(data);
            }
          ).$promise;
        };
        /**
         * @see {Domain._reload()}
         */
        self._reload = function() { self._load( self.id, self.domainId, self.deviceManager.id); };

        /**
         * Save Property State method: Configure, Allocate, Deallocate
         */
        self._commonSave = function(method, properties) {
          return RedhawkREST.device.save(
              {deviceId: self.id, managerId: self.deviceManager.id, domainId: self.domainId},
              {method: method, properties: properties},
              function(){ $timeout(self._reload, 1000); }
          );
        };
        self.configure = function(properties) { return self._commonSave('configure', properties); };
        self.allocate = function(properties) { return self._commonSave('allocate', properties); };
        self.deallocate = function(properties) { return self._commonSave('deallocate', properties); };

        self._load(id, domainId, managerId);
      };

      // External API Method for extended factories
      RedhawkDevice.prototype._updateFinished = function () { };
      return RedhawkDevice;
  }])

  /**
   * Angular-style resource that encapsulates a Device that is known to have an FEI interface
   * Extends the RedhawkDevice factory
   */
  .factory('RedhawkFeiDevice', ['RedhawkDevice', 'RedhawkREST',
    function(RedhawkDevice, RedhawkREST) {
      var RedhawkFeiDevice = function() {
        var self = this;
        RedhawkDevice.apply(self, arguments);

        // Returns a promise
        self.feiQuery = function(portId) {
          return RedhawkREST.feiDevice.query(
            {portId: portId, deviceId: self.id, managerId: self.deviceManager.id, domainId: self.domainId},
            function(data) { 
              angular.forEach(self.ports, function(port) {
                if (port.name == data.name)
                  angular.extend(port, data);
              }); 
            }
          ).$promise;
        };
      }

      RedhawkFeiDevice.prototype = Object.create(RedhawkDevice.prototype);
      RedhawkFeiDevice.prototype.constructor = RedhawkFeiDevice;
      // No change to _updateFinished

      return RedhawkFeiDevice;
    }])
  
  /**
   * Angular-style resource that encapsulates a Device that is known to have an FEI *Tuner interface
   * Extends the RedhawkDevice factory
   */
  .factory('RedhawkFeiTunerDevice', ['RedhawkDevice', 'RedhawkREST', 
    function(RedhawkDevice, RedhawkREST) {
      var RedhawkFeiTunerDevice = function() {
        var self = this;
        RedhawkDevice.apply(self, arguments);

        // Returns a promise, allocatioNId is optional.
        self.feiQuery = function(portId, allocationId) {
          return RedhawkREST.feiTunerDevice.query(
            {allocationId: allocationId, portId: portId, deviceId: self.id, managerId: self.deviceManager.id, domainId: self.domainId},
            function(data) {
              angular.forEach(self.ports, function(port) {
                if (port.name == data.name) {
                  if (port.active_allocation_ids) {
                    // data is the FEITuner structure w/ an updated allocation ID list and no id-keys filled.
                    // Find the port and remove any invalid allocation ids, then extend to update valid ones.
                    var oldIDs = UtilityFunctions.filterOldList(port.active_allocation_ids, data.active_allocation_ids);
                    for (var i=0; i < oldIDs.length; i++) {
                      delete port[oldIDs[i]];
                    }
                  }
                  angular.extend(port, data);
                }
              }); 
            }
          ).$promise;
        };

        // Returns a promise
        self.feiTune = function(portId, allocationId, properties) {
          return RedhawkREST.feiTunerDevice.tune(
              {allocationId: allocationId, portId: portId, deviceId: self.id, managerId: self.deviceManager.id, domainId: self.domainId},
              {properties: properties},
              function () { return self.feiQuery(portId, allocationId); }
          );
        };
      }

      RedhawkFeiTunerDevice.prototype = Object.create(RedhawkDevice.prototype);
      RedhawkFeiTunerDevice.prototype.constructor = RedhawkFeiTunerDevice;
      // No change to _updateFinished

      return RedhawkFeiTunerDevice;
    }])

  .factory('RedhawkSocket', ['SubscriptionSocket', 'RedhawkConfig', function(SubscriptionSocket, RedhawkConfig) {
    var statusSocket = function() {
      var socket = SubscriptionSocket.createNew();

      socket.connect(RedhawkConfig.websocketUrl + '/status', function(){
        console.log("Connected to REDHAWK Status");
      });

      return socket;
    };

    var RedhawkSocket = {};
    RedhawkSocket.status = statusSocket();
    RedhawkSocket.port = function(options, on_data, on_sri) {
      var portSocket = SubscriptionSocket.createNew();

      var url = RedhawkConfig.websocketUrl;
      // FIXME: Map these paths through redhawk-config-service to consolidate them with definitions.
      if(options.domain)
        url += '/domains/'+options.domain;
      if(options.waveform)
        url += '/applications/'+options.waveform;
      if(options.component)
        url += '/components/'+options.component;
      if(options.deviceManager)
        url += '/deviceManagers/'+options.deviceManager;
      if(options.device)
        url += '/devices/'+options.device;
      if(options.port)
        url += '/ports/'+options.port;

      url += '/bulkio';

      if(on_data)
        portSocket.addBinaryListener(on_data);
      if(on_sri)
        portSocket.addJSONListener(on_sri);

      portSocket.connect(url, function(){
        console.log("Connected to Port " + options.port);
      });

      return portSocket;
    };

    var EventChannelSocket = function(on_msg, on_connect) {
      var self = this;

      self.close = function(){
        console.log("Disconnected from Event Channel");
        self.socket.close();
      };

      var Msg = function(command, topic, domainId) {
        return {command: command, topic: topic, domainId: domainId}
      };
      self.addChannel = function(topic, domainId) {
        console.log('Adding topic "'+topic+'" for domainId "'+domainId+'."');
        self.socket.send(JSON.stringify(new Msg('ADD', topic, domainId)));
      };
      self.removeChannel = function(topic, domainId) {
        console.log('Removing topic "'+topic+'" for domainId "'+domainId+'."');
        self.socket.send(JSON.stringify(new Msg('REMOVE', topic, domainId)));
      };

      self.socket = SubscriptionSocket.createNew();
      var url = RedhawkConfig.websocketUrl + '/msg';

      self.socket.connect(url, function() {
        console.log("Connected to Event Channel");
        if(on_connect) on_connect.call(self);
      });

      if(on_msg) {
        self.socket.addJSONListener(on_msg);
      }
    };

    RedhawkSocket.eventChannel = function(on_msg, on_connect) {
      return new EventChannelSocket(on_msg, on_connect);
    };

    return RedhawkSocket;
  }])  
  /**
   * Common controller design pattern is to:
   * 1) Include `user` and `Redhawk`
   * 2) $watch(user.domain)
   * 3) Redhawk.getDomain(user.domain) 
   * Thus...might as well include this element in the client-side core.
   */
  .factory('user', ['Redhawk', function(Redhawk){
      var user = {domain: undefined};

      Redhawk.getDomainIds().$promise.then(function(data){
        user.domain = data[0];
      });
      return user;
  }])
;

// Local utility functions
var UtilityFunctions = UtilityFunctions || {
  /**
   * Adds FrontEnd JS specific data to the port data returned by the server.
   * NOTE: This is purely for identifying BULKIO Output Ports!!
   * @param ports
   */
  processPorts : function(ports) {
    var bulkioCheck = function(port) {
      var portDataTypeRegex = /^data(.*)$/;
      var matches = portDataTypeRegex.exec(port.idl.type);
      if(matches) {
        port.canPlot = port.direction == "Uses" && port.idl.namespace == "BULKIO";
        if(port.canPlot)
          port.plotType = matches[1].toLowerCase();
      } else {
        port.canPlot = false;
      }
    }

    var feiCheck = function (port) {
      if ("FRONTEND" == port.idl.namespace && "Provides" == port.direction) {
        port.canFeiQuery = true;
        port.canFeiTune = ("AnalogTuner" == port.idl.type || "DigitalTuner" == port.idl.type);
      }
      else {
        port.canFeiQuery = false;
        port.canFeiTune = false;
      }
    }
    angular.forEach(ports, function(port) {
      bulkioCheck(port);
      feiCheck(port);
    });
  },

  // Returns items in oldList not found in newList
  filterOldList : function(oldList, newList) {
    var out = [];
    var unique = true;
    for (var oldI = 0; oldI < oldList.length; oldI++) {
      for (var newI = 0; newI < newList.length; newI++) {
        if (oldList[oldI] == newList[newI]) {
          unique = false;
          break;
        }
      }
      if (unique) 
        out.push(oldList[oldI]);
      unique = true;
    }
    return out;
  },

  // Loops through a list of properties and returns the one of matching id (or undefined)
  findPropId : function (properties, propId) {
    for (var i = 0; i < properties.length; i++) {
      if (propId == properties[i].id)
        return properties[i];
    }
    return undefined;
  },
};