"""Allows acquisition of Internet weather data.
"""

import urllib2, time, json, urllib
from metar import Metar
from cache import Cache

# cache for storing NWS observations
_nws_cache = Cache()   

def getWeatherObservation(stnCode):
    """Returns a current weather observation from an NWS weather station, using the metar 
    library to parse and hold the values.  Uses the 'metar' python library.
    """

    URL = 'http://weather.noaa.gov/pub/data/observations/metar/stations/%s.TXT'

    obs = _nws_cache.get(stnCode)   # try cache first

    if obs is None:

        # try 3 times in case of download errors.
        for i in range(3):
            try:
                read_str = urllib2.urlopen(URL % stnCode).read()
                break
            except:
                _logger.info('Retry required in getWeatherObservation.')
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
            # strange characters after the api are my weather underground key
            json_str = urllib2.urlopen('http://api.wunderground.com/api/52f395599cb1a086/conditions/q/%s.json' % urllib.quote(stn)).read()
            obs = json.loads(json_str)
            _wu_cache.store(stn, obs)

        if 'current_observation' in obs:
            return obs['current_observation']
    
    # No stations were successful
    raise ValueError("No stations with data.")
