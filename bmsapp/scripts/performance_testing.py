#!/usr/local/bin/python2.7
""" Script to test the performance of the BMON server under various load conditions
"""

import threading
import time
import random
import json
import urllib3
import yaml
import requests

urllib3.disable_warnings()

req_data = yaml.load('''
select_group: 0
select_bldg: 1
select_chart: 2
select_sensor: [2, 3, 4]
averaging_time: 720
time_period: custom
start_date: 01/01/2014
end_date: 12/31/2014     # Getting one year of data
''')

def results_time():
    '''Determine average time to complete a report request.
    This returns a tuple: (average completion time in seconds, 
                           average 1 minute load,
                           average 5 minute load,
                           average 15 minute load,
                           average reading database size in bytes)
    '''
    TRIES = 5
    tc = 0.0
    load01 = 0.0
    load05 = 0.0
    load15 = 0.0
    dbsize = 0.0
    for i in range(TRIES):
        tstart = time.time()
        # Add a random parameter to avoid caching, although probably not needed
        req_data['rdm'] = random.random()  
        r = requests.get("https://bmon.ahfctest.webfactional.com/reports/results/", params=req_data, verify=False)
        tcomplete = time.time() - tstart
        res = json.loads(r.text)
        stats = res['objects'][-1][1]
        tc += tcomplete
        load01 += stats['loads'][0]
        load05 += stats['loads'][1]
        load15 += stats['loads'][2]
        dbsize += stats['dbsize']

    return tc/TRIES, load01/TRIES, load05/TRIES, load15/TRIES, dbsize/TRIES


if __name__ == '__main__':
    print results_time()
