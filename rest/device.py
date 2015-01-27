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
Rest handlers for Devices

Classes:
Device -- Get info of a specific device
"""

from redhawk.frontendInterfaces.FRONTEND import FrontendException

from tornado import gen

from handler import JsonHandler
from helper import PropertyHelper, PortHelper
from tornado import web



class Devices(JsonHandler, PropertyHelper, PortHelper):
    @gen.coroutine
    def get(self, domain_name, dev_mgr_id, dev_id=None):
        if dev_id:
            dev = yield self.redhawk.get_device(domain_name, dev_mgr_id, dev_id)

            info = {
                'name': dev.name,
                'id': dev._id,
                'started': dev._get_started(),
                'ports': self.format_ports(dev.ports),
                'frontends': FEIHelper.format_ports(dev),
                'properties': self.format_properties(dev._properties)
            }
        else:
            devices = yield self.redhawk.get_device_list(domain_name, dev_mgr_id)
            info = {'devices': devices}

        self._render_json(info)


class DeviceProperties(web.RequestHandler):

    def get(self, *args):
        self.set_status(500)
        self.write(dict(status='Device Properties handler not implemented'))

"""
FEI 2.0 Port helper
"""
class FEIHelper(object):
    @staticmethod
    def fei_provider_ports(ports):
        return [p for p in ports if p._direction == 'Provides' and p._interface.nameSpace == 'FRONTEND']

    @staticmethod
    def format_ports (dev, ports=None):
        if not ports:
            ports = FEIHelper.fei_provider_ports(dev.ports)
        return [FEIHandler.format_port(dev, p) for p in ports]

    @staticmethod
    def format_port (dev, port):
        return {
            'name': port.name,
            'type': port._interface.name
        }

"""
FEI 2.0 Port handler
"""
class FEIHandler(JsonHandler, FEIHelper):
    @gen.coroutine
    def get(self, domain_name, dev_mgr_id, dev_id, int_name=None, attr_name=None, allocation_id=None):
        dev = yield self.redhawk.get_device(domain_name, dev_mgr_id, dev_id)
        fei_ports = self.fei_provider_ports(dev.ports)

        try: 
            if int_name:
                # Get the port and emit its status properties
                port = [p for p in fei_ports if p.name == int_name]
                info = {}
                if port:
                    port = port[0]
                    if   port._interface.name == 'FrontendTuner':
                        info = get_frontendTuner_data(dev, port, attr_name, allocation_id)
                    elif port._interface.name == 'DigitalTuner':
                        info = get_digitalTuner_data(dev, port, attr_name, allocation_id)
                    elif port._interface.name == 'AnalogTuner':
                        info = get_analogTuner_data(dev, port, attr_name, allocation_id)

                    elif port._interface.name == 'RFInfo':
                        info = get_rfInfo_data(port, attr_name)
                    elif port._interface.name == 'RFSource':
                        info = get_rfSource_data(port, attr_name)

                    elif port._interface.name == 'GPS':
                        info = get_gps_data(port, attr_name)
                    elif port._interface.name == 'NavData':
                        info = get_navdata_data(port, attr_name)

                    self._render_json(info)

                else:
                    self._render_error({
                        'error': 'PortNotFound', 
                        'message': 'Unable to locate port: {0}'.format(int_name)
                    })
            else:
                info = self.format_ports(dev, fei_ports)
                self._render_json({'frontends': info})
        except (FrontendException, Exception) as e:
            self._handle_request_exception(e)

    @gen.coroutine
    def put(self, domain_name, dev_mgr_id, dev_id, int_name, attr_name=None, allocation_id=None):
        pass
        # TODO : Implement allocation and twiddling of port.ref set_whatever methods.

"""
FrontendTuner Data
"""
def get_frontendTuner_data(dev, port, attr_name=None, allocation_id=None, other_map=None):
    callback_map = { 
        'tuner_control'         : port.ref.getTunerType, 
        'tuner_device_control'  : port.ref.getTunerDeviceControl,
        'tuner_group_id'        : port.ref.getTunerGroupId,
        'tuner_rf_flow_id'      : port.ref.getTunerRfFlowId,
        'tuner_status'          : port.ref.getTunerStatus
    }
    if other_map:
        callback_map.update(other_map)
    info = {}

    if attr_name:
        if allocation_id:
            if attr_name in callback_map:
                info[attr_name] = callback_map[attr_name](allocation_id)
        else:
            info = get_frontendTuner_data(dev, port) # Invalid, return tuner_status.
    else:
        # Return frontend tuner status and valid names
        info['FRONTEND::tuner_status'] = dev.frontend_tuner_status
        info['valid_names'] = callback_map.keys()
    return info

"""
AnalogTuner Data
"""
def get_analogTuner_data(dev, port, attr_name=None, allocation_id=None, other_map=None):
    callback_map = {
        'tuner_center_frequency'    : port.ref.getTunerCenterFrequency,
        'tuner_bandwidth'           : port.ref.getTunerBandwidth,
        'tuner_agc_enable'          : port.ref.getTunerAgcEnable,
        'tuner_gain'                : port.ref.getTunerGain,
        'tuner_reference_source'    : port.ref.getTunerReferenceSource,
        'tuner_enable'              : port.ref.getTunerEnable
    }
    if other_map:
        callback_map.update(other_map)
    return get_frontendTuner_data(dev, port, attr_name, allocation_id, other_map)

"""
DigitalTuner Data
"""
def get_digitalTuner_data(dev, port, attr_name=None, allocation_id=None):
    callback_map = {
        'tuner_output_sample_rate' : port.ref.getTunerOutputSampleRate
    }
    return get_analogTuner_data(dev, port, attr_name, allocation_id, callback_map)


"""
FIXME: Probably a cleaner way to do this support method and those below it.
"""
def get_prepared_attribute(attr_name=None, options={}):
    if attr_name in options:
        return options[attr_name]
    else:
        return {'valid_names': options.keys}

"""
RFInfo Data
"""
def get_rfInfo_data(port, attr_name=None):
    return get_prepared_attribute(attr_name, {
        'rf_flow_id': port.ref._get_rf_flow_id(),
        'rfinfo_pkt': port.ref._get_rfinfo_pkt().__dict__
    })

"""
RFSource Data
"""
def get_rfSource_data(port, attr_name=None):
    return get_prepared_attribute(attr_name, {
        'available_rf_inputs': port.ref._get_available_rf_inputs().__dict__,
        'current_rf_input': port.ref._get_current_rf_input().__dict__
    })


"""
GPS Data
"""
def get_gps_data(port, attr_name=None):
    return get_prepared_attribute(attr_name, {
        'gps_info'    : port.ref._get_gps_info().__dict__,
        'gps_time_pos': port.ref._get_gps_time_pos().__dict__
    })

"""
NavData Data
"""
def get_navdata_data(port, attr_name=None):
    return get_prepared_attribute(attr_name, {
        'nav_packet': port.ref._get_nav_packet().__dict__
    })