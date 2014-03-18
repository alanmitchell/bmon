"""Class to encapsulate a BMS database.  Uses the SQLite database.
"""

import sqlite3

class BMSdata:

    def __init__(self, fname):
        """Creates the database object.
        fname: full path to SQLite database file. If the file is not present, 
            it will be created.
        """

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
        
    def close(self):
        """Closes this database object.
        """
        self.conn.close()

    def insert_reading(self, ts, id, val):
        """Inserts a record into the database.
        """
        # Check to see if sensor table exists.  If not, create it.
        if id not in self.sensor_ids:
            self.cursor.execute("CREATE TABLE [%s] (ts integer primary key, val real)" % id)
            self.sensor_ids.add(id)
        self.cursor.execute("INSERT INTO [%s] (ts, val) VALUES (?, ?)" % id, (ts, val))

        # Commits take a lot of time, but Sqlite does not allow an open database reference to be
        # shared across threads.  The web server uses multiple threads to handle requests.
        self.conn.commit()

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
        'startTime' (Unix seconds).
        """
        rec_ct = 0
        for id in self.sensor_ids:
            try:
                self.cursor.execute('SELECT COUNT(*) FROM [%s] WHERE ts > ?' % id, (startTime,))
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
