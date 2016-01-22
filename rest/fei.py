# Author: Thomas Goodwin
# Company: Geon Technologies
# Subject: FEI interface handlers.

from redhawk.frontendInterfaces.FRONTEND import FrontendException, NotSupportedException, BadParameterException

from tornado import gen, web
import json

from handler import JsonHandler
from helper import PropertyHelper, PortHelper

"""
FEI 2.0 Port helper
"""
class FEIHelper(PortHelper):
    @staticmethod
    def find_port(name, dev):
        port = [p for p in dev.ports if p.name == name]
        if port:
            return port[0]
        else:
            raise FEIPortNotFoundException(name)

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

class FEIAttributeHasNoCallbackException(FEIInterfaceTypeException):
    def __str__(self):
        return "Attribute {0} was not able to be set (no callback).".format(self.name)

"""
FEI *Tuner handler 
"""
class FEITunerHandler(JsonHandler, FEIHelper):
    @gen.coroutine
    def get(self, domain_name, dev_mgr_id, dev_id, int_name, allocation_id=None, attribute_name=None):     
        try:   
            dev = yield self.redhawk.get_device(domain_name, dev_mgr_id, dev_id)
            port = self.find_port(int_name, dev)
            info = self.format_port(port)

            if port._direction == 'Provides':
                CSV_KEY = 'FRONTEND::tuner_status::allocation_id_csv'
                tuner_statuses = dev.frontend_tuner_status
                allocations = [s[CSV_KEY].replace(" ", "").split(",") for s in tuner_statuses]
                allocations = set([a for sublist in allocations for a in sublist if a != ""])
                info['active_allocation_ids'] = list(allocations)
                info['tuner_statuses'] = [];
                for s in tuner_statuses:
                    el = []
                    for k, v in s.items():
                        el.append({
                            "id"   : k,
                            "value": v,
                            "scaType": "simple" # FIXME: Hack to make it similar to what is returned in an allocation
                            })
                    info['tuner_statuses'].append(el)

                info['allocations'] = []
                
                if allocation_id:
                    allocation_id = str(allocation_id)
                    attr = self.get_attribute(port, allocation_id, attribute_name)
                    info['allocations'].append({
                        "id"    : allocation_id,
                        "value" : attr
                        })

            self._render_json(info)

        except (FEIInterfaceTypeException, Exception) as e:
            self._handle_request_exception(e)


    @gen.coroutine
    def put(self, domain_name, dev_mgr_id, dev_id, int_name, allocation_id):
        data = json.loads(self.request.body)
        dev = yield self.redhawk.get_device(domain_name, dev_mgr_id, dev_id)
        port = self.find_port(int_name, dev)
        # FEITunerHandler supports 1 PUT: Tune.
        try:
            props = PropertyHelper.unformat_properties(data['properties'])
            for prop in props:
                self.set_attribute(port, str(allocation_id), prop['id'], prop['value'])
        except Exception as e:
            self._handle_request_exception(e)

    @staticmethod
    def get_attribute(port, allocation_id, attribute_name=''):
        cb = {}
        if   port._interface.name == 'FrontendTuner':
            cb = FEITunerHandler.general_get_callbacks(port)
        elif port._interface.name == 'AnalogTuner':
            cb = FEITunerHandler.analog_get_callbacks(port)
        elif port._interface.name == 'DigitalTuner':
            cb = FEITunerHandler.digital_get_callbacks(port)
        else:
            raise FEIInterfaceTypeException(port._interface.name)

        if attribute_name in cb:
            try:
                val = FEITunerHandler.fixobj(cb[attribute_name](allocation_id))
            except NotSupportedException:
                val = 'NOT_SUPPORTED'
            except:
                raise

            return { "id": attribute_name, "value": val }
        else:
            vals = []
            for attribute_name in cb.keys():
                vals.append(FEITunerHandler.get_attribute(port, allocation_id, attribute_name))
            return vals

    @staticmethod
    def set_attribute(port, allocation_id, attribute_name, value):
        cb = {}
        if   port._interface.name == 'FrontendTuner':
            cb = FEITunerHandler.general_set_callbacks(port)
        elif port._interface.name == 'AnalogTuner':
            cb = FEITunerHandler.analog_set_callbacks(port)
        elif port._interface.name == 'DigitalTuner':
            cb = FEITunerHandler.digital_set_callbacks(port)
        else:
            raise FEIInterfaceTypeException(port._interface.name)

        if attribute_name in cb:
            cb[attribute_name](allocation_id, value)
        else:
            raise FEIAttributeHasNoCallbackException(attribute_name)


    @staticmethod
    def general_get_callbacks(port):
        return { 
            'tuner_control'         : port.ref.getTunerType, 
            'tuner_device_control'  : port.ref.getTunerDeviceControl,
            'tuner_group_id'        : port.ref.getTunerGroupId,
            'tuner_rf_flow_id'      : port.ref.getTunerRfFlowId,
            'tuner_status'          : port.ref.getTunerStatus
        }

    @staticmethod
    def general_set_callbacks(port):
        return { }  # All generals are get-only.

    @staticmethod
    def analog_get_callbacks(port):
        d = FEITunerHandler.general_get_callbacks(port)
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
    def analog_set_callbacks(port):
        d = FEITunerHandler.general_set_callbacks(port)
        d.update({
            'tuner_center_frequency'    : port.ref.setTunerCenterFrequency,
            'tuner_bandwidth'           : port.ref.setTunerBandwidth,
            'tuner_agc_enable'          : port.ref.setTunerAgcEnable,
            'tuner_gain'                : port.ref.setTunerGain,
            'tuner_reference_source'    : port.ref.setTunerReferenceSource,
            'tuner_enable'              : port.ref.setTunerEnable
        })
        return d

    @staticmethod
    def digital_get_callbacks(port):
        d = FEITunerHandler.analog_get_callbacks(port)
        d.update({
            'tuner_output_sample_rate' : port.ref.getTunerOutputSampleRate
        })
        return d

    @staticmethod
    def digital_set_callbacks(port):
        d = FEITunerHandler.analog_set_callbacks(port)
        d.update({
            'tuner_output_sample_rate' : port.ref.setTunerOutputSampleRate
        })
        return d



class FEIOnlyAttributeBaseHandler(JsonHandler, FEIHelper):
    def _dict_struct(self, s):
        outobj = {}
        for k, v in s.__dict__.items():
            if hasattr(v, '__dict__'):
                outobj[k] = self._dict_struct(v)
            elif v != v: # NaN detection
                outobj[k] = 'NaN'
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

            # Verify interface type
            if port._interface.name not in self._interfacenames:
                raise FEIInterfaceTypeException(port._interface.name)

            if port._direction == 'Provides':
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
    _interfacenames = ['RFInfo']

    def _options(self, port):
        return {
            'rf_flow_id': port.ref._get_rf_flow_id(),
            'rfinfo_pkt': self._dict_struct(port.ref._get_rfinfo_pkt())
        }

class FEIRFSourceHandler(FEIRFInfoHandler):
    _interfacenames = ['RFSource']

    def _options(self, port):
        return {
            'available_rf_inputs': self._dict_structs(port.ref._get_available_rf_inputs()),
            'current_rf_input': self._dict_struct(port.ref._get_current_rf_input())
        }

class FEIGPSHandler(FEIOnlyAttributeBaseHandler):
    _interfacenames = ['GPS']

    def _options(self, port):
        return {
            'gps_info'    : self._dict_struct(port.ref._get_gps_info()),
            'gps_time_pos': self._dict_struct(port.ref._get_gps_time_pos())
        }

class FEINavDataHandler(FEIOnlyAttributeBaseHandler):
    _interfacenames = ['NavData']

    def _options(self, port):
        return {
            'nav_packet': self._dict_struct(port.ref._get_nav_packet())
        }