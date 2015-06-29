"""
Allows acquisition of ARIS building energy use data.

    energy_type_ids ={1: 'Electric',
                      2: 'Natural Gas',
                      3: 'Propane',
                      6: 'Coal',
                      7: 'Demand - Electric',
                      8: 'Demand - Nat Gas',
                      10: 'Steam District Ht',
                      11: 'Hot Wtr District Ht',
                      12: 'Spruce Wood',
                      13: 'Birch Wood',
                      14: '#1 Fuel Oil',
                      15: '#2 Fuel Oil'}

    energy_units   = {1: 'kWh',
                      2: 'Gallon',
                      3: 'Cord',
                      4: 'Ton',
                      5: 'CCF',
                      6: 'Btu',
                      7: 'thousand pounds'}
"""

import requests
from datetime import datetime
from dateutil import parser
from dateutil.relativedelta import *
from django.conf import settings


def get_energy_use(building_id,
                   energy_type_id,
                   last_update_ts=0,
                   energy_parameter='EnergyQuantity',
                   energy_multiplier=1,
                   expected_period_months=1):
    """
    Returns building energy usage information via the ARIS Web API

    """

    aris_url = getattr(settings, 'BMSAPP_ARIS_URL')
    aris_username = getattr(settings, 'BMSAPP_ARIS_USERNAME')
    aris_password = getattr(settings, 'BMSAPP_ARIS_PASSWORD')

    last_update_dt = datetime.utcfromtimestamp(last_update_ts + 1)

    timestamp_list = []
    values_list = []

    url = aris_url + '/api/buildingmonitoring/buildingenergyusage'
    values = {'userName': aris_username,
              'password': aris_password,
              'buildingId': building_id,
              'energyTypeId': energy_type_id,
              'LatestUpdateDate': last_update_dt}

    try:
        r = requests.post(url, data=values, headers={'Accept': 'application/json'})
        r.raise_for_status()
        response_data = r.json()
    except requests.exceptions.RequestException as e:
        print e
        raise

    if len(response_data) > 0:
        for response_row in response_data:
            # Assign the sensor date/time
            if response_row['MeterReadDate']:
                read_dt = parser.parse(response_row['MeterReadDate'])
            else:
                read_dt = datetime.strptime(response_row['UsageMonthYear'], '%m-%Y') + relativedelta(months=+1, days=-1)

            if response_row['PreviousReadDate']:
                last_dt = parser.parse(response_row['PreviousReadDate'])
                if abs((read_dt - last_dt).days) > (expected_period_months * 52):
                    last_dt = read_dt + relativedelta(months=(-1 * expected_period_months))
            else:
                last_dt = read_dt + relativedelta(months=(-1 * expected_period_months))
                # a better algorithm to deal with the last day of the month would be:
                # last_dt = read_dt + relativedelta(days=+1)
                #                   + relativedelta(months=(-1 * expected_period_months))
                #                   + relativedelta(days=-1)
                # but, changing this might mess up data from sensors that have already been processed

            sensor_dt = last_dt + (read_dt - last_dt)/2
            read_period_hours = (read_dt - last_dt).total_seconds() / 60 / 60

            # Get the value for the requested energy parameter
            if energy_parameter in response_row:
                if not response_row[energy_parameter]:
                    continue
                try:
                    energy_parameter_value = float(response_row[energy_parameter])
                except:
                    print "ARIS Value Conversion Error: ", response_row[energy_parameter]
                    continue
            else:
                print "Parameter Name Not Present: ", energy_parameter
                continue

            # Convert the energy parameter value into appropriate units for the sensor
            if energy_parameter == 'EnergyQuantity':
                # return hourly energy use
                sensor_value = energy_parameter_value * energy_multiplier / read_period_hours
            elif energy_parameter in ['DollarCost', 'DemandCost']:
                # return monthly cost. There are 8766 hours in a year, so 730.5 hours on average per month
                sensor_value = energy_parameter_value * energy_multiplier / (read_period_hours / 730.5)
            else:
                # return values for demand or anything else
                sensor_value = energy_parameter_value * energy_multiplier

            # Update the last update date
            update_dt = parser.parse(response_row['UpdateDate'])
            if update_dt > last_update_dt:
                last_update_dt = update_dt
            last_update_ts = (last_update_dt - datetime.utcfromtimestamp(0)).total_seconds()

            # Add the results to the output lists
            timestamp_list.append((sensor_dt - datetime.fromtimestamp(0)).total_seconds())
            values_list.append(sensor_value)

    return last_update_ts, timestamp_list, values_list

