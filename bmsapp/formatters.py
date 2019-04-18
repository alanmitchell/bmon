"""
This module contains formatting functions for sensor values
"""
from . import formatter_codes

def okofen2_status(coded_value):
    """Okofen Touch Pellet Boiler status codes, newer model in 
    THRHA Juneau Warehouse and THRHA Angoon Housing.
    """
    return formatter_codes.okofen2_status_codes.get(coded_value,
                                                   'Unknown Code: %s' % coded_value)

def okofen_status(coded_value):
    """Okofen Pellet Boiler status codes, older model in Haines Senior Center.
    """
    return formatter_codes.okofen_status_codes.get(coded_value,
                                                   'Unknown Code: %s' % coded_value)

def alarm_formatter(coded_value):
    """Code of 0 indicates OK, and anything else indicates an
    Alarm.  Can be used to format 0/1 values from alarm contacts.
    """
    return 'OK' if coded_value==0 else 'Alarm!'


def on_off_formatter(coded_value):
    '''Formats On/Off type sensors where the value 0 is Off, and any
    other value is On.
    '''
    if coded_value == 0:
        return 'Off'
    else:
        return 'On'


def occupied_formatter(coded_value):
    '''Use with occupancy sensors that return 0 if vacant and 
    anything else (usually 1) if occupied.
    '''
    return 'Vacant' if coded_value == 0 else 'Occupied'


def _bitmask_to_list(encoded_value, bitmask_dictionary):
    output_list = []
    for bit_offset in list(bitmask_dictionary.keys()):
        if int(encoded_value) & (1 << bit_offset):
            output_list.append(bitmask_dictionary[bit_offset])
    return output_list if len(output_list) else ['None']


def aerco_fault_code_formatter(coded_value):
    '''Used with AERCO boilers.  Formats `_fault_code' sensor from mini-monitor.
    '''
    value_list = _bitmask_to_list(coded_value, formatter_codes.aerco_fault_code_bitmask_dictionary)
    return '; '.join(map(str, value_list))


def aerco_io_status_formatter(coded_value):
    '''Used with AERCO boilers.  Formats `_io_status' sensor from mini-monitor.
    '''
    value_list = _bitmask_to_list(coded_value, formatter_codes.aerco_io_status_bitmask_dictionary)
    return '; '.join(map(str, value_list))


def aerco_boiler_status_formatter(coded_value):
    '''Used with AERCO boilers.  Formats `_boilerX_status' sensors from mini-monitor.
    '''
    if 1 <= coded_value <= 40:
        return 'Fired, sequence = ' + str(coded_value)
    elif coded_value in formatter_codes.aerco_boiler_status_dictionary:
        return formatter_codes.aerco_boiler_status_dictionary[coded_value]
    else:
        return 'Unknown Value: %s' % coded_value


def sage_limits_sensor_formatter(coded_value):
    '''Used with Sage Boiler Control (Burnham Alpine).  Formats '_limits' 
    sensor from mini-monitor.
    '''
    value_list = _bitmask_to_list(coded_value, formatter_codes.sage_limits_bitmask_dictionary)
    return '; '.join(map(str, value_list))


def sage_alarm_reason_formatter(coded_value):
    '''Used with Sage Boiler Control (Burnham Alpine).  Formats '_alarm_reason' 
    sensor from mini-monitor.
    '''
    if coded_value in formatter_codes.sage_alarm_reason_dictionary:
        return formatter_codes.sage_alarm_reason_dictionary[coded_value]
    else:
        return 'Unknown Value: %s' % coded_value


def sage_demand_source_formatter(coded_value):
    '''Used with Sage Boiler Control (Burnham Alpine).  Formats '_demand_source' 
    sensor from mini-monitor.
    '''
    if coded_value in formatter_codes.sage_demand_source_dictionary:
        return formatter_codes.sage_demand_source_dictionary[coded_value]
    else:
        return 'Unknown Value: %s' % coded_value


def sage_lockout_code_formatter(coded_value):
    '''Used with Sage Boiler Control (Burnham Alpine).  Formats '_lockout_code' 
    sensor from mini-monitor.
    '''
    if coded_value in formatter_codes.sage_lockout_code_dictionary:
        return formatter_codes.sage_lockout_code_dictionary[coded_value]
    else:
        return 'Unknown Value: %s' % coded_value


def sage_alert_code_formatter(coded_value):
    '''Used with Sage Boiler Control (Burnham Alpine).  Formats '_alarm_code' 
    and '_alert_code' sensors from mini-monitor.
    '''
    if coded_value in formatter_codes.sage_alert_code_dictionary:
        return formatter_codes.sage_alert_code_dictionary[coded_value]
    else:
        return 'Unknown Value: %s' % coded_value
