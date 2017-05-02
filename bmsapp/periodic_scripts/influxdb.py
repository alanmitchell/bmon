'''
Script to send new sensor readings to an InfluxDB time-series database.
'''

from bmsapp.readingdb import bmsdata
import bmsapp.models

def run(influx_url= '', 
        database_name='',
        username='', 
        password='',
        measurement='reading',
        value_field='value',
        reach_back=14,      # days
        ignore_last_rec=False,
        **kwargs):
    """
    Parameters
    Look to the parameter list above for default values.
    ----------
    influx_url:  The full URL to access the write method for the InfluxDB database,
        e.g. https://akstats.com/db/write .  If the database is not listening on the
        standard HTTP port, include that port in the URL as well, e.g.
        http://abc.com:8086/write .
    database_name:  The name of the InfluxDB database at this URL that you want to
        write the data into.
    username:  If authentication is enabled on the database, this is the InfluxDB 
        username that allows for writing to the target database.
    password:  The password associated with the above username.
    measurement:  The name of the measurement associated with the BMON records being 
        written.  This function only supports writing records to a single measurement 
        name.
    value_field:  The name of the InfluxDB field used to hold the sensor value.
    reach_back:  If a BMON sensor has not been posted to the InfluxDB database before,
         this parameter determines how much history of sensor readings are sent to the
         database.  The parameter is measured in days.  For example, if the parameter is
         14 days, then only 14 days of history will be posted to the InfluxDB database.
         Subsequent calls to this script only send new BMON records to the InfluxDB 
         database.
    ignore_last_rec:  This script only sends BMON sensor readings that have not already
        been sent. If this parameter is 'ignore_last_rec' parameter is True, *all* sensor
        readings, restricted by the 'reach_back' parameter are sent.  The most common use
        of this parameter is allow for more historical readings to be posted to the InfluxDB
        database.  That can be accomplished by setting a large 'reach_back' value, setting
        this 'ignore_last_rec' parameter to True, and then allowing the script to run once.
        After that run which will post a large amount of historical records, you can set 
        this 'ignore_last_rec' parameter to False and continue forward with only posting new
        BMON sensor readings.
    """

def new_records(last_rec={}, reach_back=14, chunk_size=500):
    """A Python generator function that yields a list of new sensor readings from the BMON 
    reading database and a dictionary indicating the time of the most recent reading for each
    sensor in the return records.  So the function return is a two-element tuple:
        (sensor reading list), (dictionary of timestamps of the last readings in the sensor
        reading list)
    First, here is a description of the sensor reading list element of the return value.
    This is a list of 3-element tuples, with each tuple being of the format:
        (tags, ts, value)
    where 'tags' is a dictionary of metadata about the sensor reading; for example 
    {'sensor_id': 'homer_18234', 'bldg': 'Homer-Strawbale'}.  These tags are created from
    BMON properties of the Sensor and the associated Building(s) objects. 'ts' is the Unix Epoch
    timestamp of the reading, and 'value' is the sensor reading value.
    The second element of the function return value is a dictionary that gives the Unix Epoch 
    timestamp of the most current reading for each sensor in the returned sensor reading list.
    The dictionary is keyed on the object ID of the BMON Sensor object from bmsapp.models.
    
    Input Parameters
    ----------------
    last_rec:  A dictionary that gives the Unix epoch timestamp of the most recent sensor reading
        that has already been returned.  All readings occurring after that time are returned in 
        this call to the function.  The dictionary is keyed on the object ID of the BMON Sensor object.
        The dictionary does not need to be complete; i.e. sensors can be missing from the dictionary.
    reach_back:  If the 'last_rec' dictionary does not contain a key for a sensor, then this 'reach_back'
        parameter determines how many days of sensor readings will be returned by this function.  If
        'reach_back' is set to 0, all historical readings will be included.
    chunk_size: This is the maximum number of records (3-element tuples) that will be yielded by
        this function at one time.  If there are 1200 sensor reading in total and 'chunk_size' is set
        to 500, the function will yield three times, yielding 500 records, 500 records, and 200 records.
    """

def clean_string(s, sep_char='-'):
    """Function that "cleans" a string by substituting a particular character for all whitepace
    and punctuation found in the string.  After that substitution is make, any consecutive
    occurrences of the replacement character are reduced to one occurrence.
    Returns the cleaned string.
    Input Parameters:
    -----------------
    s:  The string to clean.
    sep_char: The character to substitute in for whitespace and punctuation.
    """
    to_sub = string.whitespace + string.punctuation
    trans_table = string.maketrans(to_sub, len(to_sub) * sep_char)
    fixed = string.translate(s, trans_table)
    
    while True:
        new_fixed = fixed.replace(sep_char * 2, sep_char)
        if new_fixed == fixed:
            break
        fixed = new_fixed
    
    return fixed
