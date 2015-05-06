"""
This module contains formatting functions for sensor values
"""
import formatter_codes


def alarm_formatter(coded_value):
    """Code of 0 indicates OK, and anything else indicates an
    Alarm.  Can be used to format 0/1 values from alarm contacts.
    """
    return 'OK' if coded_value==0 else 'Alarm!'


def _bitmask_to_list(encoded_value, bitmask_dictionary):
    output_list = []
    for bit_offset in bitmask_dictionary.keys():
        if int(encoded_value) & (1 << bit_offset):
            output_list.append(bitmask_dictionary[bit_offset])
    return output_list if len(output_list) else ['None']


def aerco_fault_code_formatter(coded_value):
    value_list = _bitmask_to_list(coded_value, formatter_codes.aerco_fault_code_bitmask_dictionary)
    return '; '.join(map(str, value_list))


def aerco_io_status_formatter(coded_value):
    value_list = _bitmask_to_list(coded_value, formatter_codes.aerco_io_status_bitmask_dictionary)
    return '; '.join(map(str, value_list))


def aerco_boiler_status_formatter(coded_value):
    if 1 <= coded_value <= 40:
        return 'Fired, sequence = ' + str(coded_value)
    elif coded_value in formatter_codes.aerco_boiler_status_dictionary:
        return formatter_codes.aerco_boiler_status_dictionary[coded_value]
    else:
        return 'Unknown (invalid value)'


def sage_limits_sensor_formatter(coded_value):
    value_list = _bitmask_to_list(coded_value, formatter_codes.sage_limits_bitmask_dictionary)
    return '; '.join(map(str, value_list))


def on_off_formatter(coded_value):
    if coded_value == 0:
        return 'Off'
    else:
        return 'On'


def sage_alarm_reason_formatter(coded_value):
    if coded_value in formatter_codes.sage_alarm_reason_dictionary:
        return formatter_codes.sage_alarm_reason_dictionary[coded_value]
    else:
        return 'Unknown (invalid value)'


def sage_demand_source_formatter(coded_value):
    if coded_value in formatter_codes.sage_demand_source_dictionary:
        return formatter_codes.sage_demand_source_dictionary[coded_value]
    else:
        return 'Unknown (invalid value)'


def sage_lockout_code_formatter(coded_value):
    if coded_value in formatter_codes.sage_lockout_code_dictionary:
        return formatter_codes.sage_lockout_code_dictionary[coded_value]
    else:
        return 'Unknown (invalid value)'


def sage_alert_code_formatter(coded_value):
    if coded_value in formatter_codes.sage_alert_code_dictionary:
        return formatter_codes.sage_alert_code_dictionary[coded_value]
    else:
        return 'Unknown (invalid value)'
