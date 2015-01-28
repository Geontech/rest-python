# Author: Thomas Goodwin
# Company: Geon Technologies
# Subject: FEI interface handlers.

from redhawk.frontendInterfaces.FRONTEND import FrontendException, NotSupportedException

from tornado import gen, web

from handler import JsonHandler
from helper import PropertyHelper

"""
FEI 2.0 Port helper
"""
class FEIHelper(object):
    @staticmethod
    def fei_provider_ports(ports):
        return [p for p in ports if p._direction == 'Provides' and p._interface.nameSpace == 'FRONTEND']

    @staticmethod
    def find_port(name, dev):
        port = [p for p in dev.ports if p.name == name]
        if port:
            return port[0]
        else:
            raise FEIPortNotFoundException(name)

    @staticmethod
    def format_ports (dev, ports=None):
        if not ports:
            ports = FEIHelper.fei_provider_ports(dev.ports)
        return [FEIHandler.format_port(p) for p in ports]

    @staticmethod
    def format_port (port):
        return {
            'name': port.name,
            'type': port._interface.name
        }

    @staticmethod
    def fixobj (obj):
        if isinstance(obj, set):
            obj = list(obj)
        if isinstance(obj, list):
            if len(obj) > 0:
                if hasattr(obj[0], 'value') and hasattr(obj[0], 'id'):
                    obj = PropertyHelper.format_properties(obj)
        return obj


"""
FEI Exceptions
"""
# Indicates the port._interface.name doesn't match expectations in the handler
class FEIInterfaceTypeException(Exception):
    def __init__(self, name=''):
        self.name = name

    def __str__(self):
        return "Interface type was not recognized in the handler: {0}".format(self.name)

class FEIPortNotFoundException(FEIInterfaceTypeException):
    def __str__(self):
        return "Port was not found on the device: {0}".format(self.name)


"""
FEI 2.0 Port handler (general)
"""
class FEIHandler(JsonHandler, FEIHelper):
    @gen.coroutine
    def get(self, domain_name, dev_mgr_id, dev_id):
        dev = yield self.redhawk.get_device(domain_name, dev_mgr_id, dev_id)
        info = self.format_ports(dev)
        self._render_json({'frontends': info})

"""
FEI *Tuner handler 
"""
class FEITunerHandler(JsonHandler, FEIHelper):
    @gen.coroutine
    def get(self, domain_name, dev_mgr_id, dev_id, int_name, allocation_id=None, attribute_name=None):     
        try:   
            dev = yield self.redhawk.get_device(domain_name, dev_mgr_id, dev_id)
            port = self.find_port(int_name, dev)
            info = {}

            if allocation_id:
                info['id'] = allocation_id
                allocation_id = str(allocation_id)
                info.update(self.call_with_id(port, allocation_id, attribute_name))
            else:
                # Return tuner statuses and an easy-to-use list of all allocation ids found.
                info = self.format_port(port)
                CSV_KEY = 'FRONTEND::tuner_status::allocation_id_csv'
                tuner_statuses = list(dev.frontend_tuner_status)
                info['frontend_tuner_status'] = self.fixobj(tuner_statuses)

                allocations = [s[CSV_KEY].replace(" ", "").split(",") for s in tuner_statuses]
                allocations = list(set([a for sublist in allocations for a in sublist if a != ""]))
                info['allocations'] = list(set(allocations)) or []

            self._render_json(info)

        except (FEIInterfaceTypeException, Exception) as e:
            self._handle_request_exception(e)

    @staticmethod
    def call_with_id(port, allocation_id, attribute_name=''):
        cb = {}
        if   port._interface.name == 'FrontendTuner':
            cb = FEITunerHandler.general_callbacks(port)
        elif port._interface.name == 'AnalogTuner':
            cb = FEITunerHandler.analog_callbacks(port)
        elif port._interface.name == 'DigitalTuner':
            cb = FEITunerHandler.digital_callbacks(port)
        else:
            raise FEIInterfaceTypeException(port._interface.name)
        if attribute_name in cb:
            try:
                val = FEITunerHandler.fixobj(cb[attribute_name](allocation_id))
            except NotSupportedException:
                val = 'NOT_SUPPORTED'
            finally:
                return {attribute_name: val}
        else:
            vals = {}
            for attribute_name in cb.keys():
                vals.update(FEITunerHandler.call_with_id(port, allocation_id, attribute_name))
            return vals

    @staticmethod
    def general_callbacks(port):
        return { 
            'tuner_control'         : port.ref.getTunerType, 
            'tuner_device_control'  : port.ref.getTunerDeviceControl,
            'tuner_group_id'        : port.ref.getTunerGroupId,
            'tuner_rf_flow_id'      : port.ref.getTunerRfFlowId,
            'tuner_status'          : port.ref.getTunerStatus
        }

    @staticmethod
    def analog_callbacks(port):
        d = FEITunerHandler.general_callbacks(port)
        d.update({
            'tuner_center_frequency'    : port.ref.getTunerCenterFrequency,
            'tuner_bandwidth'           : port.ref.getTunerBandwidth,
            'tuner_agc_enable'          : port.ref.getTunerAgcEnable,
            'tuner_gain'                : port.ref.getTunerGain,
            'tuner_reference_source'    : port.ref.getTunerReferenceSource,
            'tuner_enable'              : port.ref.getTunerEnable
        })
        return d

    @staticmethod
    def digital_callbacks(port):
        d = FEITunerHandler.analog_callbacks(port)
        d.update({
            'tuner_output_sample_rate' : port.ref.getTunerOutputSampleRate
        })
        return d



class FEIOnlyAttributeBaseHandler(JsonHandler, FEIHelper):
    def _dict_struct(self, s):
        outobj = {}
        for k, v in s.__dict__.items():
            if hasattr(v, '__dict__'):
                outobj[k] = self._dict_struct(v)
            else:
                outobj[k] = v
        return outobj

    def _dict_structs(self, ss):
        outobj = []
        for s in ss:
            outobj.append(self._dict_struct(s))
        return outobj

    @gen.coroutine
    def get(self, domain_name, dev_mgr_id, dev_id, int_name, attribute_name=None): 
        try:       
            dev = yield self.redhawk.get_device(domain_name, dev_mgr_id, dev_id)
            port = self.find_port(int_name, dev)
            info = self.format_port(port)

            options = self._options(port)
            if attribute_name in options:
                info[attribute_name] = self.fixobj(options[attribute_name])
            else:
                for k,v in options.items():
                    info[k] = self.fixobj(v)
            self._render_json(info)
        except (FEIPortNotFoundException, Exception) as e:
            self._handle_request_exception(e)

    def _options(self, port):
        return {}



class FEIRFInfoHandler(FEIOnlyAttributeBaseHandler):
    def _options(self, port):
        return {
            'rf_flow_id': port.ref._get_rf_flow_id(),
            'rfinfo_pkt': self._dict_struct(port.ref._get_rfinfo_pkt())
        }

class FEIRFSourceHandler(FEIRFInfoHandler):
    def _options(self, port):
        return {
            'available_rf_inputs': self._dict_structs(port.ref._get_available_rf_inputs()),
            'current_rf_input': self._dict_struct(port.ref._get_current_rf_input())
        }

class FEIGPSHandler(FEIOnlyAttributeBaseHandler):
    def _options(self, port):
        return {
            'gps_info'    : self._dict_struct(port.ref._get_gps_info()),
            'gps_time_pos': self._dict_struct(port.ref._get_gps_time_pos())
        }

class FEINavDataHandler(FEIOnlyAttributeBaseHandler):
    def _options(self, port):
        return {
            'nav_packet': self._dict_struct(port.ref._get_nav_packet())
        }