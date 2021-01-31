"""Periodic script to collect readings from AmbientWeather weather stations.
AmbientWeather provides API access to the data.
"""
import requests

def run(application_key: str, api_key: str, **kwargs) -> dict:

    # collecting the data from the ambient weather site for a sensor
    # gathered into a json file format
    api_url = 'https://api.ambientweather.net/v1/devices'
    payload = dict(applicationKey=application_key, apiKey=api_key)
    response = requests.get(api_url, params=payload)
    response_body = response.json()
  
    # Empty list created to hold all reading data from all sensors.
    sensors_reading_list = []

    for sensor in response_body:
        # dicts with the neccesary information from api repsonse
        mac_address = sensor['macAddress'].replace(':','')
        sensor_data = sensor['lastData']

        # desired sensor data values for extraction
        # hard wire values here for extraction
        desired_data_keys = ["windgustmph","winddir_avg10m", "windspdmph_avg10m", "tempf", "humidity", "baromrelin", "baromabsin", "tempinf", "humidityin", "hourlyrainin", "solarradiation"]
        data_log_timestamp = int(sensor_data['dateutc'] / 1000)

        # extracting data from api response and adding proper key names for value
        for key in desired_data_keys:
            if key in sensor_data.keys():
                sensor_id = mac_address + '_' + key
                sensor_data_value = sensor_data[key]
                
                sensor_data_tuple = (data_log_timestamp, sensor_id, sensor_data_value)
                
                # appending timestamp sensor data values to readings list
                sensors_reading_list.append(sensor_data_tuple)      
        
    # return of function in dict form for bmon data  
    return {'readings': sensors_reading_list}    
