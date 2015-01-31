"""Class to encapsulate the BMON Reading database.  Uses the SQLite database.
"""

import sqlite3
import sys
import os.path
import time
import shutil
import subprocess
import glob
import calendar
import pytz
from dateutil import parser


# The path to the default Sqlite database used to store readings.
DEFAULT_DB = os.path.join(os.path.dirname(__file__), 'data', 'bms_data.sqlite')


class BMSdata:

    def __init__(self, fname=DEFAULT_DB):
        """Creates the database object.
        fname: full path to SQLite database file. If the file is not present, 
            it will be created.
        """

        self.db_fname = fname   # save database filename.

        self.conn = sqlite3.connect(fname)

        # use the SQLite Row row_factory for all Select queries
        self.conn.row_factory = sqlite3.Row

        # now create a cursor object
        self.cursor = self.conn.cursor()
        
        # make a set list of all of the tables (sensor IDs + special tables
        # with names starting with underbar) in the database, so
        # that it is fast to determine whether a sensor exists in the current
        # database.
        recs = self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        self.sensor_ids = set([rec['name'] for rec in recs])  # plus special tables
        
        # Check to see if the table that stores last raw reading for cumulative
        # counter sensors exists.  If not, make it.  Make the value field a 
        # real instead of integer in case this table is needed for non counter
        # sensors in the future.
        if '_last_raw' not in self.sensor_ids:
            self.cursor.execute("CREATE TABLE [_last_raw] (id varchar(50) primary key, ts integer, val real)")
            self.conn.commit()

    def __del__(self):
        """Used to ensure that database is closed when this object is destroyed.
        """
        self.close()
        
    def close(self):
        """Closes this database object.  This is called in the destructor for this object.
        """
        self.conn.close()

    def add_sensor_table(self, sensor_id):
        """Adds a table to hold readings from a sensor with the id 'sensor_id'.  Also
        adds the id to the set that holds sensor ids.
        """
        self.cursor.execute("CREATE TABLE [%s] (ts integer primary key, val real)" % sensor_id)
        self.conn.commit()
        self.sensor_ids.add(sensor_id)

    def insert_reading(self, ts, id, val):
        """Inserts a record or records into the database.  'ts', 'id', and
        'val' can either be lists or single values.  If val is None, it is 
        not stored in the database and it is recorded as an exception.
        """
        try:
            recs = zip(ts, id, val)
        except:
            # they were single values, not lists
            recs = [(ts, id, val)]
        
        exceptions = ''
        success_count = 0
        for one_ts, one_id, one_val in recs:
            try:
                # Check to see if sensor table exists.  If not, create it.
                if one_id not in self.sensor_ids:
                    self.add_sensor_table(one_id)
                if one_val is not None:    # don't store None values
                    self.cursor.execute("INSERT INTO [%s] (ts, val) VALUES (?, ?)" % one_id, (one_ts, one_val))
                    success_count += 1
                else:
                    exceptions += '\nNone value not stored with reading %s, %s, %s' % (one_ts, one_id, one_val)
            except:
                exceptions += '\nError with reading %s, %s, %s: %s' % (one_ts, one_id, one_val, sys.exc_info()[1])

        # Commits take a lot of time, but Sqlite does not allow an open database reference to be
        # shared across threads.  The web server uses multiple threads to handle requests.
        self.conn.commit()
        
        msg = '%s readings stored successfully%s' % (success_count, exceptions)
        
        if len(exceptions):
            # Raise an error if there were any exceptions.  This ensures an 
            # entry will be stored in the error log file.
            raise ValueError(msg)
        else:
            return msg
        

    def last_read(self, sensor_id):
        """Returns the last reading for a particular sensor.  
        The reading is returned as a row dictionary.
        Returns None if no readings are available for the requested sensor.
        """
        # address case where sensor id does not exist
        if sensor_id not in self.sensor_ids:
            return None

        self.cursor.execute('SELECT * FROM [%s] ORDER BY ts DESC LIMIT 1' % sensor_id)
        row = self.cursor.fetchone()
        return dict(row) if row else None

    def rowsForOneID(self, sensor_id, start_tm=None, end_tm=None):
        """Returns a list of dictionaries, each dictionary having a 'ts' and 'val' key.  The
        rows are for a particular sensor ID, and can be further limited by a time range.
        'start_tm' and 'end_tm' are UNIX timestamps.  If either are not provided, no limit
        is imposed.  The rows are returned in timestamp order.
        """
        # address case where sensor id does not exist
        if sensor_id not in self.sensor_ids:
            return []

        sql = 'SELECT ts, val FROM [%s] WHERE 1' % sensor_id
        if start_tm is not None:
            sql += ' AND ts>=%s' % int(start_tm)
        if end_tm is not None:
            sql += ' AND ts<=%s' % int(end_tm)
        sql += ' ORDER BY ts'

        self.cursor.execute(sql)
        return [dict(r) for r in self.cursor.fetchall()]

    def readingCount(self, startTime=0):
        """Returns the number of readings in the reading table inserted after the specified
        'startTime' (Unix seconds) and before now (in case erroneously timestamped readings
        are in the file).
        """
        rec_ct = 0
        for id in self.sensor_ids:
            try:
                self.cursor.execute('SELECT COUNT(*) FROM [%s] WHERE ts > ? and ts < ?' % id, (startTime, time.time()))
                rec_ct += self.cursor.fetchone()[0]
            except:
                # not all tables are reading tables and may error out cause no 'ts' column
                pass
        return rec_ct
        
    def replaceLastRaw(self, sensor_id, ts, val):
        """Replaces the last raw reading stored in the '_last_raw' table for
        'sensor_id' and returns the timestamp and value that were there prior 
        to replacement. If no last reading was present for the sensor, None 
        values are returned.
        """
        self.cursor.execute('SELECT * FROM [_last_raw] WHERE id = ?', (sensor_id,))
        rec = self.cursor.fetchone()
        if rec:
            # remember last values and then replace them with a SQL update
            last_ts = rec['ts']
            last_val = rec['val']
            
            self.cursor.execute('''UPDATE [_last_raw] SET ts = ?, val = ? 
                                   WHERE id = ?''', (ts, val, sensor_id))
            self.conn.commit()
            return last_ts, last_val
            
        else:
            # There was no record for this sensor_id.  Make one.
            self.cursor.execute('''INSERT INTO [_last_raw] (id, ts, val) 
                                   VALUES (?, ?, ?)''', (sensor_id, ts, val))
            self.conn.commit()
            return None, None   # no prior values

    def backup_db(self, days_to_retain):
        """Backs up the database and compresses the backup.  Deletes old backup
        files that were created more than 'days_to_retain' ago.
        """
        # make backup filename with current date time in 'bak' subdirectory
        fname = os.path.join(os.path.dirname(self.db_fname), 'bak', time.strftime('%Y-%m-%d-%H%M%S') + '.sqlite')

        # Before copying the database file, need to force a lock on it so that no
        # write operations occur during the copying process

        # create a dummy table to write into.
        try:
            self.cursor.execute('CREATE TABLE _junk (x integer)')
        except:
            # table already existed
            pass

        # write a value into the table to create a lock on the database
        self.cursor.execute('INSERT INTO _junk VALUES (1)')

        # now copy database
        shutil.copy(self.db_fname, fname)

        # Rollback the Insert as we don't really need it.
        self.conn.rollback()

        # gzip the backup file
        subprocess.call(['gzip', fname])

        # delete any backup files more than 'days_to_retain' old.
        cutoff_time = time.time() - days_to_retain * 24 *3600.0
        for fn in glob.glob(os.path.join(os.path.dirname(self.db_fname), 'bak', '*.gz')):
            if os.path.getmtime(fn) < cutoff_time:
                os.remove(fn)

    def import_text_file(self, filename, tz_name='US/Alaska'):
        """Adds the sensor reading data present in the tab-delimited 'filename' to 
        the reading database. Date/time values in the file are assumed to be in the
        'tz_name' time zone.

        The file must be tab-delimited and the values in the first column must be date/time 
        strings interpretable by the Python dateutil parser module.  Subsequent columns 
        must contain sensor reading values; the each item can be blank or contain a value parseable 
        by the Python float function. The first non-blank row of the file must contain sensor IDs 
        (the first column of that row can contain anything, as it is the timestamp column). An
        exmaple of the format is (white space separation between columns need to be the Tab
        character):

            ts                 id_2341   test_alarm_code
            4/12/2014 13:23    2.2       44.3
            4/12/2014 13:33    3.2       41.1

        The method returns a two tuple.  The first item is the number of readings successfully
        stored, and the second is a list of errors, each item being an error description string.
        """

        # make a timezone object
        tz = pytz.timezone(tz_name)

        # list of errors that occurred while processing file
        errors = []

        first_row = True
        vals_stored = 0
        cur_line = 0    # current line number being processed
        for lin in open(filename):

            cur_line += 1

            # ignore blank lines
            if len(lin.strip())==0:
                continue

            flds = lin.strip().split('\t')

            # Process sensor IDs in the first row
            if first_row:
                # get the sensor ids in this file
                file_sensor_ids = [fld.strip() for fld in flds[1:]]

                # if any are not present in the database, create tables for them
                for s_id in file_sensor_ids:
                    if s_id not in self.sensor_ids:
                        self.add_sensor_table(s_id)
                first_row = False
                continue

            try:
                # get date and convert to UNIX timestamp
                datestr = flds[0]
                dt = parser.parse(datestr)
                dt_aware = tz.localize(dt)
                ts = calendar.timegm(dt_aware.utctimetuple())
            except:
                errors.append("Problem parsing date %s at line %s" % (datestr, cur_line))
                continue

            # loop through sensor values and store
            for s_id, val in zip(file_sensor_ids, flds[1:]):
                try:
                    if len(val.strip())!=0:
                        float_val = float(val)
                        if float_val is not None:     # sometimes find "nan" in data
                            self.cursor.execute("INSERT INTO [%s] (ts, val) VALUES (?, ?)" % s_id, (ts, float(val)))
                            vals_stored += 1
                except Exception as e:
                    errors.append("Problem storing %s: %s=%s at line %s: %s" % (datestr, s_id, val, cur_line, e))

        self.conn.commit()
        return vals_stored, errors
