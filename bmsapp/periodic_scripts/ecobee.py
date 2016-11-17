"""
Script to collect data from Ecobee thermostats.  The data collection function
is named "run" and is called by the "scripts/run_periodic_scripts.py" module.
This module also contains a couple functions that are used during the initial
authorization process that is required for access to an Ecobee account.  Those
functions are called by the "views.ecobee_auth" function.
"""
from django.conf import settings
import requests


def run(**kwargs):
    """
    Gathers temperature, humidity and run-time data from an Ecobee account.  This function
    is called by "scripts/run_periodic_scripts.py".

    Parameters
    ----------
    kwargs

    Returns
    -------

    """
    return {}

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

    # The Authorization URL for Ecobee
    AUTH_URL = 'https://api.ecobee.com/authorize'

    # Get the api key needed to acquire a PIN
    api_key = settings.BMSAPP_ECOBEE_API_KEY

    # parameters needed to get a PIN
    params = {'response_type': 'ecobeePin', 'client_id': api_key, 'scope': 'smartRead'}

    # Request the PIN and convert the JSON results to a Python dictionary
    results = requests.get(AUTH_URL, params=params).json()

    return results

def get_tokens(auth_code):
    """
    Requests an access and refresh token from the Ecobee API.

    Parameters
    ----------
    auth_code

    Returns
    -------

    """

    # The Token request URL for Ecobee
    AUTH_URL = 'https://api.ecobee.com/token'

    # Get the api key
    api_key = settings.BMSAPP_ECOBEE_API_KEY

    # parameters needed to request tokens
    params = {'grant_type': 'ecobeePin', 'client_id': api_key, 'code': auth_code}

    # Request the Tokens
    response = requests.post(AUTH_URL, params=params)
    if response.status_code == requests.codes.ok:
        results = response.json()
        return True, results['access_token'], results['refresh_token']
    else:
        return False, None, None
