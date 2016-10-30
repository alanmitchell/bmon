'''
Script to collect sensor readings from an OkoFEN pellet boiler.
'''
import random, time

def run(**kwargs):
    results = {'readings': [(None, 'anc_birch_wind', 10.0 * random.random()),
                            (None, 'anc_birch_temp', 40 + 20 * random.random())]}
    return results
