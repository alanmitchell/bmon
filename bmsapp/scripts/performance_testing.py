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
averaging_time: 168
time_period: custom
start_date: 01/01/2014
end_date: 12/31/2014     # Getting one year of data
''')

def time_query(no_query=False):
    '''Determine average time to complete a report request.
    This returns a tuple: (average completion time in seconds, 
                           average 1 minute load,
                           average 5 minute load,
                           average 15 minute load,
                           average reading database size in bytes)
    if 'no_query' is True, no actual queries are performed, and instead
    this function delays for a roughly equivalent amount of time.
    '''
    TRIES = 10
    tc = 0.0
    load01 = 0.0
    load05 = 0.0
    load15 = 0.0
    dbsize = 0.0
    resp_size = 0.0
    if no_query:
        time.sleep(TRIES * 0.7)

    else:
        for i in range(TRIES):
            tstart = time.time()
            # Add a random parameter to avoid caching, although probably not needed
            req_data['rdm'] = random.random()  
            r = requests.get("https://bmon.ahfctest.webfactional.com/reports/results/", params=req_data, verify=False)
            resp = r.text
            tcomplete = time.time() - tstart
            res = json.loads(resp)
            stats = res['objects'][-1][1]
            tc += tcomplete
            load01 += stats['loads'][0]
            load05 += stats['loads'][1]
            load15 += stats['loads'][2]
            dbsize += stats['dbsize']
            resp_size += len(resp)

    return tc/TRIES, load01/TRIES, load05/TRIES, load15/TRIES, dbsize/TRIES, resp_size/TRIES


class ReadingPoster(threading.Thread):
    '''Posts sensor readings
    '''

    def __init__ (self, delay, bldg_ct, sensor_ct):
        """
        'delay': delay between reading posts.  Randomness is added
            to cause delay to vary from 0 to 2 x 'delay'
        'bldg_ct': for creating random sensor IDs, the total building count
        'sensor_ct': for creating random sensor IDs, the # of sensors per building
        The timestamp used in each post is random.  The value is always 1.0.
        """  
        # run constructor of base class
        threading.Thread.__init__(self)

        self.url = 'https://bmon.ahfctest.webfactional.com/readingdb/reading/%s/store/'
        self.delay = delay
        self.bldg_ct = bldg_ct
        self.sensor_ct = sensor_ct
        
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

            # create a random sensor ID and the needed posting URL
            sensor_id = '%03d_%03d' % (random.randint(0, self.bldg_ct - 1), random.randint(0, self.sensor_ct - 1))
            url = self.url % sensor_id
            dt_new = dt_base + datetime.timedelta(seconds=random.random()*1e7)
            data['ts'] = dt_new.strftime('%Y-%m-%d %H:%M:%S')
            requests.get(url, params=data, verify=False)
            self.reading_count += 1
            # delay a random amount of time that averages to the requested delay.
            time.sleep(self.delay * 2.0 * random.random())


def query_under_load(thread_count, reading_delay, building_count, bldg_sensor_count, no_query=False):
    '''Times the response of chart query while simultaneous posting
    sensor readings to the database.
    'thread_count': number of sensor reading posting threads.
    'reading_delay': delay between postings for one thread.
    'building_count': for creating random sensor IDs, the total building count
    'bldg_sensor_count': for creating random sensor IDs, the # of sensors per building
    'no_query': if True, no chart queries are performed, but sensor reading postings are;
        this is way to measure maximum posting rate under no query load.
    '''

    posters = []
    tstart = time.time()
    for i in range(thread_count):
        poster = ReadingPoster(reading_delay, building_count, bldg_sensor_count)
        posters.append(poster)
        poster.start()

    time.sleep(reading_delay)
    results =  time_query(no_query)

    t_elapsed = time.time() - tstart
    total_reads = 0
    for p in posters:
        p.stop_posting()
        total_reads += p.reading_count
        del p

    #print '%.1f posts / second' % (total_reads / t_elapsed)
    time.sleep(reading_delay + 1.0)  # wait for threads to exit cleanly?

    return [total_reads / t_elapsed] + list(results)


if __name__ == '__main__':

    #args = sys.argv
    #thread_count = int(args[1]) if len(args)>=2 else 5
    #rdg_delay = float(args[2]) if len(args)>=3 else 0.0

    # (threads, delay between sensor posts)
    post_params = (
        (1, 1.0, False),
        (3, 0.5, False),
        (5, 0.5, False),
        (10, 0.5, False),
        (10, 0.25, False),
        (10, 0.15, False),
        (10, 0.0, False),
        (10, 0.0, True)
    )
    param_len = len(post_params)

    i = 0
    while True:
        thread_count, rdg_delay, no_query = post_params[i % param_len]
        results = query_under_load(thread_count, rdg_delay, 8, 9, no_query)
        results = [time.time(), thread_count, rdg_delay] + results
        res_str = '\t'.join(['%.2f' % val for val in results])
        open('performance.txt', 'a').write(res_str + '\n')
        i += 1
        time.sleep(25)
