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
Provides static classes to format for REST

Classes:
PropertyHelper -- Convert CORBA and RH Sandbox Properties into dictionaries (more descriptive than prop_to_dict)
PortHelper -- Convert Port information into dict
"""

from ossie.properties import __TYPE_MAP as CF_TYPE_MAP
from ossie.utils.prop_helpers import Property, simpleProperty, structProperty, structSequenceProperty, sequenceProperty

class PropertyHelper(object):

    """ For going from REDHAWK to JSON """
    @staticmethod
    def format_properties(propertySet, properties=None):
        if propertySet and any(isinstance(p, Property) for p in propertySet):
            # If properties was also provided, filter the property set
            if properties:
                propertySet = PropertyHelper._filter_propertySet(propertySet, properties)
            
            return PropertyHelper._property_set(propertySet)
        elif properties:
            return PropertyHelper._corba_properties(properties)
        else:
            return []

    @staticmethod
    def _corba_properties(properties):
        prop_list = []
        for prop in properties:
            ret = PropertyHelper.__any(prop)
            prop_list.append(ret)

        return prop_list

    @staticmethod
    def _clean_name(prop):
        if hasattr(prop, 'clean_name') and prop.clean_name.strip():
            clean_name = prop.clean_name
        else:
            clean_name = prop.id.split('::')[-1]
        return clean_name

    @staticmethod
    def _filter_propertySet(propertySet, properties):
        filteredPropertySet = []

        for propertySetItem in propertySet:
            for prop in properties:
                if propertySetItem.id == prop.id:
                    filteredPropertySet.append(propertySetItem)
                    break

        return filteredPropertySet

    @staticmethod
    def _property_set(properties):
        def _handle_simple(prop):
            val = prop.defValue

            try:
                tempVal = prop.queryValue()

                if tempVal != None:
                    val = tempVal
            except:
                pass

            clean_name = PropertyHelper._clean_name(prop)

            p_dict = {
                'id'        : prop.id,
                'name'      : clean_name,
                'scaType'   : 'simple',
                'value'     : val,
                'type'      : prop.type,
                'mode'      : prop.mode,
                'kinds'     : prop.kinds
            }

            if hasattr(prop, '_enums') and prop._enums:
                p_dict['enumerations'] = prop._enums
            return p_dict

        def _handle_simpleseq(prop):
            p_dict = _handle_simple(prop)
            p_dict['scaType'] = 'simpleSeq'
            return p_dict

        def _handle_struct(prop):
            p_dict = _handle_simple(prop)
            p_dict.pop('type', None)
            p_dict['value'] = []
            for _, m in prop.members.iteritems():
                if type(m) == sequenceProperty:
                    p_dict['value'].append( _handle_simpleseq(m) )
                else:
                    p_dict['value'].append( _handle_simple(m) )
            p_dict['scaType'] = 'struct'
            return p_dict

        def _handle_structseq(prop):
            p_dict = _handle_simple(prop)
            p_dict['value'] = []
            for idx, _ in enumerate(prop):
                element_dict = _handle_struct(prop[idx])
                p_dict['value'].append( element_dict )
            p_dict['scaType'] = 'structSeq'
            return p_dict

        prop_list = []
        for prop in properties:
            if type(prop) == simpleProperty:
                prop_list.append( _handle_simple(prop) )
            elif type(prop) == sequenceProperty:
                prop_list.append( _handle_simpleseq(prop) )
            elif type(prop) == structProperty:
                prop_list.append( _handle_struct(prop) )
            elif type(prop) == structSequenceProperty:
                prop_list.append( _handle_structseq(prop) )
        return prop_list

    """ Going from JSON to REDHAWK Properties """
    @staticmethod
    def unformat_properties(properties):
        def _handle_value(val):
            out_val = val
            if type(val) == list:
                out_val = []
                for v in val:
                    if type(v) == dict:
                        if type(out_val) == list:
                            out_val = {} # Change to map
                        out_val.update({v['id']: _handle_value(v.get('value', None))})
                    else:
                        out_val.append(v)
            return out_val

        props_dict = {}
        for prop in properties:
            props_dict[prop['id']] = _handle_value(prop.get('value', None))
        return props_dict

    """ Going from JSON to ANY """
    @staticmethod
    def unformat_properties_without_query(properties):
        def _handle_value(val):
            out_val = val
            # Struct or Simple Sequence (Struct Sequence not currently supported)
            if type(val) == list:
                # Struct
                if len(val) > 0 and type(val[0]) == dict:
                    isStruct = False

                    out_val = {}

                    for idValPair in val:
                        out_val[idValPair.get('id')] = idValPair.get('value', None)
                #Simple Sequence or empty
                else:
                    pass
            # Simple
            return out_val

        props_dict = {}
        for prop in properties:
            props_dict[prop['id']] = _handle_value(prop.get('value', None))
        return props_dict

    ###############################################
    # Private

    @staticmethod
    def __any_simple(corba_any):
        return {
            'id': corba_any.id,
            'name': PropertyHelper._clean_name(corba_any),
            'scaType': 'simple',
            'value': corba_any.value.value(),
            'type': PropertyHelper.__corba_to_cf_type(corba_any.value._t)
            }

    @staticmethod
    def __any_struct(corba_any):
        ret = {
            'id': corba_any.id,
            'name': PropertyHelper._clean_name(corba_any),
            'scaType': 'struct',
            'value': []
            }
        for a in corba_any.value.value():
            if 'orb.create_sequence_tc' in str(a.value._t):
                ret['value'].append(PropertyHelper.__any_simple_seq(a))
            else:
                ret['value'].append(PropertyHelper.__any_simple(a))
        return ret

    @staticmethod
    def __any_simple_seq(corba_any):
        ret = {
            'id': corba_any.id,
            'name': PropertyHelper._clean_name(corba_any),
            'scaType': 'simpleSeq',
            'type': '',
            'value': []
            }
        for a in corba_any.value.value():
            if hasattr(a, 'value'):
                # The item in the sequence is a CORBA type
                if ret['type'] == '':
                    ret['type'] = PropertyHelper.__corba_to_cf_type(a.value._t)
                ret['value'].append(a.value.value())
            else:
                # The item in the sequence is a Python type
                if ret['type'] == '':
                    # Convert to CF type
                    aType = str(type(a))
                    if 'str' in aType:
                        ret['type'] = 'string'
                    elif ('int' in aType) or ('long' in aType):
                        ret['type'] = 'long'
                    elif 'float' in aType:
                        ret['type'] = 'double'
                    elif 'bool' in aType: 
                        ret['type'] = 'boolean'
                    else:
                        ret['type'] = aType
                ret['value'].append(a)
        return ret

    @staticmethod
    def __any_struct_seq(corba_any):
        ret = {
            'id': corba_any.id,
            'name': PropertyHelper._clean_name(corba_any),
            'scaType': 'structSeq',
            'value': []
            }
        for a in corba_any.value.value():
            value = []
            for m in a.value():
                value.append(PropertyHelper.__any_struct(m))
            ret['value'].append(value)
        return ret

    @staticmethod
    def __any(corba_any):
        type_name = str(corba_any.value._t)

        if 'CORBA.TypeCode("IDL:CF/Properties:1.0")' == type_name:
            return PropertyHelper.__any_struct(corba_any)
        elif 'CORBA.TypeCode("IDL:omg.org/CORBA/AnySeq:1.0")' == type_name:
            # Struct sequence
            if len(corba_any.value.value()) != 0 and 'CORBA.TypeCode("IDL:CF/Properties:1.0")' == str(corba_any.value.value()[0]._t):
                return PropertyHelper.__any_struct_seq(corba_any)
            # Simple sequence or empty struct sequence
            else:
                return PropertyHelper.__any_simple_seq(corba_any)
        else:
            return PropertyHelper.__any_simple(corba_any)

    @staticmethod
    def __corba_to_cf_type(ctype):
        __FLIPPED_TYPE_MAP = {v[1] : (v[0], k) for (k, v) in CF_TYPE_MAP.iteritems() if not k.startswith('w')}
        return __FLIPPED_TYPE_MAP[ctype][1]


class PortHelper(object):

    @staticmethod
    def format_ports(ports):
        return [PortHelper.format_port(port) for port in ports]

    @staticmethod
    def format_port(port):
        port_value = {'name': port.name, 'direction': port._direction}
        portFn = None
        if port._direction == 'Uses':
			portFn = port._using
        else:
            portFn = port._interface
        
        version_idx = portFn.repoId.rfind(':')
        version = portFn.repoId[version_idx:]
        port_value['repId'] = portFn.repoId
        port_value['idl'] = {
            'type': portFn.name,
            'namespace': portFn.nameSpace,
            'version': version
        }
        return port_value
