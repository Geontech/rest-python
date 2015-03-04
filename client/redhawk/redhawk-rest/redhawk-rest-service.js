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
angular.module('RedhawkREST', ['ngResource', 'RedhawkConfig'])
  .service('RedhawkREST', ['$resource', 'RedhawkConfig', function($resource, RedhawkConfig) {
    this.domain = $resource(RedhawkConfig.domainsUrl, {}, {
      query:        {method: 'GET', cache:false},
      add:          {method: 'POST'},
      info:         {method: 'GET', url: RedhawkConfig.domainUrl, cache:false},
      configure:    {method: 'PUT', url: RedhawkConfig.domainUrl + '/configure'},
      // FIXME: This path does not exist in the server handler list or handler logic.
      events:       {method: 'GET', url: RedhawkConfig.domainUrl + '/eventChannels', isArray:true, cache:false}
    });
    this.fileSystem = $resource(RedhawkConfig.domainUrl + '/fs/:path', {}, {
      query:        {method: 'GET', cache:false}
    });
    this.deviceManager = $resource(RedhawkConfig.deviceManagerUrl, {}, {
      query:        {method: 'GET', cache:false}
    });
    this.device = $resource(RedhawkConfig.deviceUrl, {}, {
      query:        {method: 'GET', cache:false},
      save:         {method: 'PUT', url: RedhawkConfig.deviceUrl + '/properties'},
      feiQuery:     {method: 'GET', url: RedhawkConfig.devicePortUrl, cache:false},
      feiQueryId:   {method: 'GET', url: RedhawkConfig.devicePortUrl + '/:allocationId', cache:false},
      feiTune:      {method: 'PUT', url: RedhawkConfig.devicePortUrl + '/:allocationId'}
    });
    this.waveform = $resource(RedhawkConfig.waveformsUrl, {}, {
      query:        {method: 'GET',    url: RedhawkConfig.waveformUrl, cache:false},
      status:       {method: 'GET',    url: RedhawkConfig.waveformsUrl, cache:false},
      launch:       {method: 'POST',   url: RedhawkConfig.waveformsUrl},
      release:      {method: 'DELETE', url: RedhawkConfig.waveformUrl},
      update:       {method: 'POST',   url: RedhawkConfig.waveformUrl},
      configure:    {method: 'PUT',    url: RedhawkConfig.waveformUrl + '/properties'}
    });
    this.component = $resource(RedhawkConfig.componentUrl, {}, {
      query:        {method: 'GET', cache:false},
      configure:    {method: 'PUT', url: RedhawkConfig.componentUrl + '/properties'}
    });
  }]);
