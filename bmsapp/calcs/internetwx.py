"""Allows acquisition of Internet weather data.
"""

import urllib.request
import urllib.error
import urllib.parse
import json
import urllib.request
import urllib.parse
import urllib.error
from django.conf import settings
from .cache import Cache

import pandas as pd
import numpy as np
from datetime import datetime
from dateutil.rrule import rrule, DAILY
import requests

# cache for storing NWS observations
_nws_cache = Cache()

def getWeatherObservation(stnCode):
    """Returns a current weather observation from an NWS weather station, using the JSON
    weather API provided by the National Weather Service.
    """
    obs = _nws_cache.get(stnCode)   # try cache first

    if obs is None:

        headers = {
            "User-Agent": "BMON (alan@analysisnorth.com)"
        }
        url = f"https://api.weather.gov/stations/{stnCode}/observations/latest"

        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            obs = response.json()
            _nws_cache.store(stnCode, obs)
        else:
            raise Exception('Could not access %s.' % stnCode)

    return obs


# cache for storing Weather Underground observations
_wu_cache = Cache()

def getWUobservation(stnList):
    """Returns a current weather observation (dictionary) retrieved from weather underground.
    Google Weather Underground API for more info.  
    'stnList' is a list of Weather Underground stations.  The first one to provide a valid
    current observation is used.
    """

    for stn in stnList:
        # ignore None stations
        if stn is None:
            continue

        # retrieve from cache, if there.
        obs = _wu_cache.get(stn)

        if obs is None:
            # not in cache; download from weather underground.
            wu_key = getattr(settings, 'BMSAPP_WU_API_KEY', None)
            if wu_key:
                url = 'http://api.wunderground.com/api/%s/conditions/q/%s.json' % (
                    wu_key, urllib.parse.quote(stn))
                json_str = urllib.request.urlopen(url, timeout=7.0).read().decode('utf-8')
                obs = json.loads(json_str)
                _wu_cache.store(stn, obs)
            else:
                raise ValueError(
                    'No Weather Underground API key in Settings File.')

        if 'current_observation' in obs:
            return obs['current_observation']

    # No stations were successful
    raise ValueError("No stations with data.")


def getMesonetTimeseries(stnID, parameter, last_ts):
    """Returns weather observations (dictionary) retrieved from mesowest.

    'stnID' is the Mesonet Station ID.
    'parameter' might include: air_temp or wind_speed or wind_gust or solar_radiation

    Returns a dictionary of of timestamp and value lists.
    """

    results = []
    for dt in rrule(DAILY, dtstart=datetime.fromtimestamp(last_ts).date(), until=datetime.utcnow().date()):

        params = {'output': 'csv',
                'stn': stnID,
                'unit': 0,
                'daycalendar':1,
                'hours': 1,
                'day1': dt.day,
                'month1': dt.month,
                'year1': dt.year,
                'time': 'GMT',
                'hour1': 23,
                'var_0': parameter,
                }
        url = 'https://mesowest.utah.edu/cgi-bin/droman/download_api2_handler.cgi?' + urllib.parse.urlencode(params)

        df = pd.read_csv(url,comment='#')
        results.append(df)

    df = pd.concat(results)

    df = df[df.Station_ID == stnID]
    df['date_time'] = pd.to_datetime(df['Date_Time']).values.astype(np.int64) // 10 ** 9
    df[parameter + '_set_1'] = df[parameter + '_set_1'].astype(float)

    df = df[df.date_time > last_ts]

    return df[['date_time',parameter + '_set_1']].to_dict(orient='list')
