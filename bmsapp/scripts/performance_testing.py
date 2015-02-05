#!/usr/local/bin/python2.7
""" Script to test the performance of the BMON server under various load conditions
"""

import threading
import time
import sys
import datetime
import random
import json
import yaml
import requests

requests.packages.urllib3.disable_warnings()

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


class ReadingPoster(threading.Thread):
    '''Posts sensor readings
    '''

    def __init__ (self, sensor_id, delay=0.0):
        """
        'sensor_id': the sensor_id to use in the post
        'delay': delay between reading posts.  Randomness is added
            to cause delay to vary from 0 to 2 x 'delay'
        The timestamp used in each post is random.  The value is always 1.0.
        """  
        # run constructor of base class
        threading.Thread.__init__(self)

        self.url = 'https://bmon.ahfctest.webfactional.com/readingdb/reading/%s/store/' % sensor_id
        self.delay = delay
        
        # If only thing left running are daemon threads, Python will exit.
        self.daemon = True

        # controls whether thread continues to post
        self.stop = False

        # counts number of readings posted
        self.reading_count = 0

    def stop_posting(self):
        '''Call to stop thread from posting.
        '''
        self.stop = True

    def run(self):

        data = {'storeKey': 'StorageKey', 'val': 1.0}
        dt_base = datetime.datetime.now()

        while True:

            if self.stop:
                return

            # delay a random amount of time that averages to the requested delay.
            time.sleep(self.delay * 2.0 * random.random())

            dt_new = dt_base + datetime.timedelta(seconds=random.random()*1e7)
            data['ts'] = dt_new.strftime('%Y-%m-%d %H:%M:%S')
            requests.get(self.url, params=data, verify=False)
            self.reading_count += 1


if __name__ == '__main__':
    #print results_time()

    TOT_POST_TIME = 5.0   # seconds
    posters = []
    for i in range(5):
        sensor_id = 'test_%03d' % i
        poster = ReadingPoster(sensor_id, 0.0)
        posters.append(poster)
        poster.start()

    time.sleep(TOT_POST_TIME)

    total_reads = 0
    for p in posters:
        p.stop_posting()
        total_reads += p.reading_count

    print '%.1f posts / second' % (total_reads / TOT_POST_TIME)
