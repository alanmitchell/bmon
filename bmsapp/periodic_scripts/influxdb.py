'''
Script to send new sensor readings to an InfluxDB time-series database.
'''
import time
import string
from bmsapp.readingdb import bmsdata
from bmsapp.models import Sensor, Building, BldgToSensor

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

    # Error Handling!

    # remember to sort the keys

    # cleaning up the name and
    # value of each tag and making both strings.  Use underbars in tag names
    # and dashes in the values instead of whitespace or punctuation.
    #    for ky, val in sensor.key_properties().items():
    #       sensor_tags[clean_string(str(ky), '_')] = clean_string(str(val), '-')

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
    The dictionary is keyed on a 2-tuple of the object ID of the BMON Sensor and the BMON
    BldgToSensor link object.
    
    Input Parameters
    ----------------
    last_rec:  A dictionary that gives the Unix epoch timestamp of the most recent sensor reading
        that has already been returned.  All readings occurring after that time are returned in 
        this call to the function.  The dictionary is keyed on a tuple of the the object ID of 
        the BMON Sensor object and the BMON BldgToSensor object.
        The dictionary does not need to be complete; i.e. sensors can be missing from the dictionary.
    reach_back:  If the 'last_rec' dictionary does not contain a key for a sensor, then this 'reach_back'
        parameter determines how many days of sensor readings will be returned by this function.  If
        'reach_back' is set to 0, all historical readings will be included.
    chunk_size: This is the maximum number of records (3-element tuples) that will be yielded by
        this function at one time.  If there are 1200 sensor reading in total and 'chunk_size' is set
        to 500, the function will yield three times, yielding 500 records, 500 records, and 200 records.
    """

    rd_list = []     # list of sensor readings to return
    last_ts = {}     # tracks timestamp of last record yielded

    # starting timestamp to use if a sensor is not in last_ts.
    if reach_back != 0:
        reach_back_ts = time.time() - reach_back * 24 * 3600
    else:
        # get all the records because reach_back was set to 0.
        reach_back_ts = 0

    # the database object that allows access to the sensor reading database
    read_db = bmsdata.BMSdata()
    
    # Loop through every sensor

    for sensor in Sensor.objects.all():

        # the list of tags for this sensor
        sensor_tags = sensor.key_properties()

        # loop through all buildings associated with this sensor.  We will send the 
        # sensor readings multiple times if there are multiple associated buildings.
        for bl_sens_link in BldgToSensor.objects.filter(sensor=sensor):
            
            # the list of tags for the associated building
            bldg_tags = bl_sens_link.building.key_properties()

            # add a tag to this set for the Sensor Group that the sensor is in
            bldg_tags['sensor_group'] = bl_sens_link.sensor_group.title

            # combine the sensor and building tags together for the final set of tags
            # for this sensor/building combo.
            final_tags = sensor_tags.copy()
            final_tags.update(bldg_tags)

            # get the starting timestamp for this sensor
            start_ts = last_rec.get((sensor.id, bl_sens_link.id), reach_back_ts) + 1    # adding one cuz database call is inclusive

            # loop through all the sensor readings
            for rec in read_db.rowsForOneID(sensor.sensor_id, start_tm = start_ts):
                ts = int(rec['ts'])
                rd_list.append( (final_tags, ts, rec['val']) )
                last_ts[(sensor.id, bl_sens_link.id)] = ts
                if len(rd_list) == chunk_size:
                    yield rd_list, last_ts
                    rd_list = []
                    last_ts = {}

    # if any remaining records, yield them
    if len(rd_list):
        yield rd_list, last_ts

def clean_string(s, sep_char='-'):
    """Function that "cleans" a string by substituting a particular character for whitepace,
    commas, and equal signs.  These are special characters to InfluxDB; they could be escaped
    but it was decided to substitute a character for them. After that substitution is make, 
    any consecutive occurrences of the replacement character are reduced to one occurrence.
    Returns the cleaned string.
    Input Parameters:
    -----------------
    s:  The string to clean.
    sep_char: The character to substitute in for whitespace and punctuation.
    """
    to_sub = string.whitespace + ',='
    trans_table = string.maketrans(to_sub, len(to_sub) * sep_char)
    fixed = string.translate(s, trans_table)
    
    while True:
        new_fixed = fixed.replace(sep_char * 2, sep_char)
        if new_fixed == fixed:
            break
        fixed = new_fixed
    
    return fixed
