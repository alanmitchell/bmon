"""Allows acquisition of Internet weather data.
"""

import urllib2, time, json, urllib
from django.conf import settings
from metar import Metar
from cache import Cache

# cache for storing NWS observations
_nws_cache = Cache()   

def getWeatherObservation(stnCode):
    """Returns a current weather observation from an NWS weather station, using the metar 
    library to parse and hold the values.  Uses the 'metar' python library.

    ** NOTE: It is possible to eliminate use of the metar python library by downloading
       decoded observations.  The URL for decoded observations is:
       http://tgftp.nws.noaa.gov/data/observations/metar/decoded/PANC.TXT
       Notice that the 'TXT' is capitalized.  The format of the file is one item
       per line.
    """

    # This is URL where the raw METAR observations are kept.  A station code
    # substitutes for the %s.
    URL = 'http://tgftp.nws.noaa.gov/data/observations/metar/stations/%s.TXT'

    obs = _nws_cache.get(stnCode)   # try cache first

    if obs is None:

        # try 3 times in case of download errors.
        for i in range(3):
            try:
                read_str = urllib2.urlopen(URL % stnCode).read()
                break
            except:
                # wait before retrying
                time.sleep(1)

        if 'read_str' not in locals():
            # retries must have failed if there is no 'read_str' variable.
            raise Exception('Could not access %s.' % stnCode)

        obs = Metar.Metar('\n'.join( read_str.splitlines()[1:] ))  # second line onward
        _nws_cache.store(stnCode, obs)

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
                url = 'http://api.wunderground.com/api/%s/conditions/q/%s.json' % (wu_key, urllib.quote(stn))
                json_str = urllib2.urlopen(url).read()
                obs = json.loads(json_str)
                _wu_cache.store(stn, obs)
            else:
                raise ValueError('No Weather Underground API key in Settings File.')

        if 'current_observation' in obs:
            return obs['current_observation']
    
    # No stations were successful
    raise ValueError("No stations with data.")
