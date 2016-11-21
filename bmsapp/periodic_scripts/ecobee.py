"""
Script to collect data from Ecobee thermostats.  The data collection function
is named "run" and is called by the "scripts/run_periodic_scripts.py" module.
This module also contains a couple functions that are used during the initial
authorization process that is required for access to an Ecobee account.  Those
functions are called by the "views.ecobee_auth" function.
"""
import json
import traceback
from django.conf import settings
import requests
from datetime import datetime
import calendar

# ----- URLS and API KEY

# The Authorization URL for Ecobee
AUTH_URL = 'https://api.ecobee.com/authorize'

# The Token request URL for Ecobee
TOKEN_URL = 'https://api.ecobee.com/token'

# Get the api key.  Don't raise an error if it is not present;
# When EcobeeDataCollector is instantiated, it will detect a lack of
# the key and produced an error message.
try:
    API_KEY = settings.BMSAPP_ECOBEE_API_KEY
except:
    # This also enables use outside of Django, as you can:
    #    import ecobee
    #    ecobee.API_KEY = 'xyz....'  # set API key directly
    API_KEY = ''

def run(access_token='', refresh_token='', include_occupancy=False, **kwargs):
    """
    See EcobeeDataCollector class for documentation of input parameters.

    Returns
    -------
    A dictionary of results, including new sensor readings, hidden access and refresh tokens,
    and a request to delete the access and refresh token script parameters.
    """

    # Use a EcobeeDataCollector object to do the work of collecting the data
    data_collector = EcobeeDataCollector(API_KEY, access_token, refresh_token, include_occupancy)

    return data_collector.data_results()


class EcobeeDataCollector:
    """
    Gathers temperature, humidity and run-time data from an Ecobee account.
    """
    def __init__(self, api_key, access_token, refresh_token, include_occupancy=False):
        """
        Parameters
        ----------
        At the time of the first run of this script, there must be a Access token and a Refresh
        token present in the script parameters.  These are manually copied into the script parameters
        from the results of the authorization process accessed at the "ecobee_auth" URL.  For
        subsequent runs of the script, the script results from the prior run will provide the
        necessary access and refresh tokens.  These tokens may have been refreshed in the prior
        run of the script, so the original tokens will be invalid.

        api_key: The 32 character BMON API Key acquired from the Ecobee Developer portal.
        access_token: 32 character access token created by the Ecobee authorization process.
            This is provided through the Script Parameters sys admin entry on the first run,
            and then provided by Hidden Script Results on subsequent runs. (the value in the
            script parameters box is automatically deleted by this script).
        refresh_token: 32 character refresh token created by the Ecobee authorization process.
            This is provided through the Script Parameters sys admin entry on the first run,
            and then provided by Hidden Script Results on subsequent runs. (the value in the
            script parameters box is automatically deleted by this script).
        include_occupancy: If True, occupancy data from the thermostat and remote sensors will
            be collected.
        """

        # There must be access and refresh tokens present and 32 characters long.
        if not type(access_token) in (str, unicode) or not type(refresh_token) in (str, unicode) or \
                        len(access_token)!=32 or len(refresh_token)!=32:
            raise ValueError('The Access or Refresh token is not present or invalid.  Reauthorize the BMON application with Ecobee at the "ecobee_auth" URL, and enter the new Access and Refresh token in the Script Parameters input box.')

        if type(api_key)!=str or len(api_key)!=32:
            raise ValueError('API Key is not present or valid.  It should be entered in the Django Settings file.')

        if type(include_occupancy)!=bool:
            raise ValueError("The 'include_occupancy' parameter must be 'True' or 'False'")

        # store the parameters for use by the results() method
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.api_key = api_key
        self.include_occupancy = include_occupancy

    def data_results(self):
        """Returns a dictionary of results, including new sensor readings, hidden access and refresh tokens,
        and a request to delete the access and refresh token script parameters.
        """

        # Start a dictionary of return results
        results = {}

        # Start a readings list
        readings = []

        try:

            # Get the data from the thermostats
            for stat in self.get_thermostats():

                # get the serial number for this thermostat (as a string)
                stat_id = str(stat['identifier']) + '_'

                # get the UNIX timestamps for the three readings present in the
                # ExtendedRuntime object.  The three readings are for three 5-minute
                # intervals.  The timestamp of the last interval is given as a string.
                # It marks the beginning of the interval, so I shift it forward to the middle
                # of the interval here.
                last_ts_str = stat['extendedRuntime']['lastReadingTimestamp']
                last_ts = self.ts_from_datestr(last_ts_str)
                tstamps = (last_ts - 450, last_ts - 150, last_ts + 150)

                # get temperature values
                vals = stat['extendedRuntime']['actualTemperature']
                vals = [val / 10.0 for val in vals]   # they are expressed in tenths, so convert
                readings += zip(tstamps, (stat_id+'temp',)*3, vals)

                # get heating setpoints
                vals = stat['extendedRuntime']['desiredHeat']
                vals = [val / 10.0 for val in vals]  # they are expressed in tenths, so convert
                readings += zip(tstamps, (stat_id + 'heat_setpoint',) * 3, vals)

                # get Humidity values
                vals = stat['extendedRuntime']['actualHumidity']
                readings += zip(tstamps, (stat_id + 'rh',) * 3, vals)

                # get temperature values
                vals = stat['extendedRuntime']['auxHeat1']
                # convert to fractional runtime from seconds / 5 minute interval
                vals = [val / 300.0 for val in vals]
                readings += zip(tstamps, (stat_id + 'heat1_run',) * 3, vals)

                # Loop through ther Remote Sensors collection, extracting data available there.
                # Use the lastStatusModified timestamp as the indicator of the time of these
                # readings.
                sensor_ts_str = stat['runtime']['lastStatusModified']
                sensor_ts = self.ts_from_datestr(sensor_ts_str)
                for sensor in stat['remoteSensors']:
                    # variables determining whether we will store particular types of readings
                    # for this sensor.
                    use_temp = False
                    use_occupancy = False
                    sens_id = ''        # the ID prefix to use for this sensor
                    if sensor['type'] == 'ecobee3_remote_sensor':
                        use_temp = True
                        use_occupancy = self.include_occupancy
                        sens_id = '%s%s_' % (stat_id, str(sensor['code']))

                    elif sensor['type'] == 'thermostat':
                        use_temp = False    # we already gathered temperature for the main thermostat
                        use_occupancy = self.include_occupancy
                        sens_id = stat_id

                    # loop through reading types of this sensor and store the requested ones
                    for capability in sensor['capability']:
                        if capability['type'] == 'temperature' and use_temp:
                            readings.append((sensor_ts, sens_id + 'temp', float(capability['value'])/10.0))
                        elif capability['type'] == 'occupancy' and use_occupancy:
                            val = 1 if capability['value'] == 'true' else 0
                            readings.append((sensor_ts, sens_id + 'occup', val))

        except:
            # Store information about the error that occurred
            results['script_error'] = traceback.format_exc()

        finally:
            # We may have some valid access and refresh tokens, so we need to return
            # the results variable even in cases of errors so the tokens are preserved.
            # Store the tokens for use the next time this script is called.  Request to delete the tokens
            # out of the Script Parameters box.
            results['hidden'] = {'access_token': self.access_token, 'refresh_token': self.refresh_token}
            results['delete_params'] = ['access_token', 'refresh_token']
            results['readings'] = readings
            return results

    def get_thermostats(self):
        """Makes a request to the API to get information about all of the registered
        thermostats in the account.
        Returns
        -------
        Returns a Python list of all of the thermostat objects in the account.
        This can require multiple HTTP calls if there are more than 25 thermostats.
        """
        THERMOSTAT_URL = 'https://api.ecobee.com/1/thermostat'
        header = {'Content-Type': 'application/json;charset=UTF-8',
                  'Authorization': 'Bearer ' + self.access_token}
        select = dict(selectionType='registered',
                      includeRuntime=True,
                      includeExtendedRuntime=True,
                      includeSensors=True,
                      )
        page = 1
        tstats = []     # the list of thermostats to return
        while True:   # Loop until no more pages
            body = {'selection': select, 'page': {'page': page}}
            params = {'body': json.dumps(body)}
            resp = requests.get(THERMOSTAT_URL, headers=header, params=params)

            # Check for an expired access token and refresh if necessary.
            if resp.status_code == 500 and resp.json()['status']['code'] == 14:
                self.refresh_tokens()
                # call again to get thermostat data
                header = {'Content-Type': 'application/json;charset=UTF-8',
                          'Authorization': 'Bearer ' + self.access_token}
                resp = requests.get(THERMOSTAT_URL, headers=header, params=params)

            # If we don't have a valid response now, we're in trouble. Error out
            if resp.status_code != requests.codes.ok:
                raise Exception('Error retrieving thermostat data: ' + resp.text)

            result = resp.json()
            tstats += result['thermostatList']
            if result['page']['totalPages'] <= page:
                # All done
                break
            page += 1

        return tstats

    def refresh_tokens(self):
        """
        Gets a new access and refresh token.

        Parameters
        ----------
        refresh_token: A valid refresh token

        Returns
        -------
        A 2-tuple of (access token, refresh token).  If an error occurs
        it is raised to the calling routine.
        """
        TOKEN_URL = 'https://api.ecobee.com/token'
        params = {'grant_type': 'refresh_token',
                  'refresh_token': self.refresh_token,
                  'client_id': self.api_key}
        response = requests.post(TOKEN_URL, params=params)
        if response.status_code == requests.codes.ok:
            result = response.json()
            self.access_token = result['access_token']
            self.refresh_token = result['refresh_token']
        else:
            raise Exception('Error occurred trying to refresh tokens:' + response.text)

    @staticmethod
    def ts_from_datestr(utc_date_str):
        """Retunns a UNIX timestamp in seconds from a string in the format
        YYYY-MM-DD HH:MM:SS, where the string is a UTC date/time.
        """
        dt = datetime.strptime(utc_date_str, '%Y-%m-%d %H:%M:%S')
        return calendar.timegm(dt.timetuple())


# ----------- Code below here is used by the Ecobee Authorization process
#             that is initiated in the views.ecobee_auth() function.

def get_pin():
    """
    Acquires a PIN so that a Ecobee Account owner can authorize the BMON app to
    acquire data.

    Returns
    -------
    A dictionary of results from the PIN request.  The most important keys are the
    'ecobeePin' (the PIN) and the 'code" (the authorization code).  Also returned
    are 'scope' ('smartRead' in this case), 'expires_in' (minutes to expiration),
    and 'interval' (minimum interval between polling for a token) key/value pairs.
    """
    # parameters needed to get a PIN
    params = {'response_type': 'ecobeePin', 'client_id': API_KEY, 'scope': 'smartRead'}

    # Request the PIN and convert the JSON results to a Python dictionary
    results = requests.get(AUTH_URL, params=params).json()

    return results

def get_tokens(auth_code):
    """
    Requests an access and refresh token from the Ecobee API.

    Parameters
    ----------
    auth_code: This is the Ecobee authorization code that was returned when the PIN
        was requested.

    Returns
    -------
    Returns a 3-tuple:
        success: a boolean indicating whether the token request succeeded
        access_token: a 32 character access token, or None if request wasn't successful
        refresh_token: a 32 character refresh token, or None if request wasn't successful
    """
    # parameters needed to request tokens
    params = {'grant_type': 'ecobeePin', 'client_id': API_KEY, 'code': auth_code}

    # Request the Tokens
    response = requests.post(TOKEN_URL, params=params)
    if response.status_code == requests.codes.ok:
        results = response.json()
        return True, results['access_token'], results['refresh_token']
    else:
        return False, None, None
