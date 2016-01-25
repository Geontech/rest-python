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

from ossie.utils.prop_helpers import Property, simpleProperty, structProperty, structSequenceProperty, sequenceProperty


class PropertyHelper(object):

    """ For going from REDHAWK to JSON """
    @staticmethod
    def format_properties(properties):
        if not properties:
            return []
        elif any(isinstance(p, Property) for p in properties):
            return PropertyHelper._property_set(properties)
        else:
            return PropertyHelper._corba_properties(properties)

    @staticmethod
    def _corba_properties(properties):
        prop_list = []
        for prop in properties:
            ret = PropertyHelper.__any(prop.value)
            ret['id'] = prop.id
            prop_list.append(ret)

        return prop_list

    @staticmethod
    def _property_set(properties):
        def _handle_simple(prop):
            try:
                val = prop.queryValue()
            except:
                val = None

            if hasattr(prop, 'clean_name'):
                clean_name = prop.clean_name
            else:
                clean_name = prop.id.split('::')[-1]

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
                m_dict = _handle_simple(m)
                p_dict['value'].append( m_dict )
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

    ###############################################
    # Private

    @staticmethod
    def __any_simple(corba_any):
        return {'scaType': 'simple', 'value': corba_any._v}

    @staticmethod
    def __any_struct(corba_any):
        ret = {'scaType': 'struct'}
        value = {}
        for a in corba_any._v:
            value[a.id] = a.value._v
        ret['value'] = value
        return ret

    @staticmethod
    def __any_seq(corba_any):
        ret = {'scaType': 'seq', 'value': []}
        for a in corba_any._v:
            ret['value'].append(PropertyHelper.__any(a))
        return ret

    @staticmethod
    def __any(corba_any):
        type_name = str(corba_any._t)

        if 'CORBA.TypeCode("IDL:CF/Properties:1.0")' == type_name:
            return PropertyHelper.__any_struct(corba_any)
        elif 'CORBA.TypeCode("IDL:omg.org/CORBA/AnySeq:1.0")' == type_name:
            return PropertyHelper.__any_seq(corba_any)
        else:
            return PropertyHelper.__any_simple(corba_any)


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
