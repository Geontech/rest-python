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
angular.module('RedhawkConfig', [])
  .provider('RedhawkConfig', [function(){
    var getWSBasePath = function() {
      var loc = window.location, new_uri;
      if (loc.protocol === "https:") {
        new_uri = "wss:";
      } else {
        new_uri = "ws:";
      }
      new_uri += "//" + loc.host;

      return new_uri;
    };

    this.restPath = '/rh/rest';
    this.wsPath = '/rh/rest';
    this.websocketUrl = getWSBasePath() + this.wsPath;
    this.restUrl = this.restPath;

    // General locations
    this.portsUrl = '/ports';
    this.portUrl = this.portsUrl + '/:portId';

    // Full URL helper paths for redhawk-rest-service, etc.
    this.domainsUrl = this.restUrl + '/domains';
    this.domainUrl = this.domainsUrl + '/:domainId';
    this.deviceManagerUrl = this.domainUrl + '/deviceManagers/:managerId';
    this.deviceUrl = this.deviceManagerUrl + '/devices/:deviceId';
    this.devicePortsUrl = this.deviceUrl + this.portsUrl;
    this.devicePortUrl = this.deviceUrl + this.portUrl;
    this.waveformsUrl = this.domainsUrl + '/waveforms';
    this.waveformUrl = this.waveformsUrl + '/:waveformId';
    this.componentsUrl = this.waveformUrl + '/components';
    this.componentUrl = this.componentsUrl + '/:componentId';

    this.setLocation = function(host, port, basePath) {
      this.restUrl = "http://" + host + (port? ':'+port: '') + (basePath? '/'+basePath: '') + this.restPath;
      this.websocketUrl = 'ws://'+ host + (port? ':'+port: '') + (basePath? '/'+basePath: '') + this.wsPath;
    };

    var provider = this;
    this.$get = function() {
      return {
        restPath:         provider.restPath,
        websocketPath:    provider.wsPath,
        websocketUrl:     provider.websocketUrl,
        restUrl:          provider.restUrl,
        domainsUrl:       provider.domainsUrl,
        domainUrl:        provider.domainUrl,
        deviceManagerUrl: provider.deviceManagerUrl,
        deviceUrl:        provider.deviceUrl,
        devicePortUrl:    provider.devicePortUrl,
        waveformsUrl:     provider.waveformsUrl,
        waveformUrl:      provider.waveformUrl,
        componentUrl:     provider.componentUrl
      };
    };
  }]);
