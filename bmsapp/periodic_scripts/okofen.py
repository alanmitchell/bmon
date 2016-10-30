'''
Script to collect sensor readings from an OkoFEN pellet boiler.
'''
import random, time

def run(**kwargs):
    time.sleep(random.random() * 2.0)
    print kwargs
    return {'Random Number': random.random()}
