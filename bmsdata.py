'''
Class to encapsulate a BMS database.  Uses the SQLite database
'''

import sqlite3, time

class BMSdata:

    def __init__(self, fname):
        '''
        fname: full path to SQLite database file. If the file is not present, 
            it will be created.
        '''

        self.conn = sqlite3.connect(fname)

        # use the SQLite Row row_factory for all Select queries
        self.conn.row_factory = sqlite3.Row

        # now create a cursor object
        self.cursor = self.conn.cursor()
        
        # make a set list of all of the tables (sensor IDs) in the database, so
        # that it is fast to determine whether a sensor exists in the current
        # database.
        recs = self.cursor.execute("SELECT tbl_name FROM sqlite_master WHERE type='table'").fetchall()
        self.sensor_ids = set([rec['tbl_name'] for rec in recs])
        
        # track when the last commit() occurred.  Used to avoid frequent, 
        # time-consuming commits when many new readings are arriving.
        self.last_commit = time.time()

    def close(self):
        self.conn.commit()  # may be lingering uncommitted sensor readings.
        self.conn.close()

    def insert_reading(self, ts, id, val):
        '''
        Inserts a record into the database.
        '''
        # Check to see if sensor table exists.  If not, create it.
        if id not in self.sensor_ids:
            self.cursor.execute("CREATE TABLE [%s] (ts integer primary key, val real)" % id)
            self.sensor_ids.add(id)
        self.cursor.execute("INSERT INTO [%s] (ts, val) VALUES (?, ?)" % id, (ts, val))
        
        # Commit if it has been more than 10 seconds since last commit.
        if time.time() > self.last_commit + 10:
            self.conn.commit()
            self.last_commit = time.time()

    def last_read(self, id):
        '''
        Returns the last reading for a particular sensor.  The reading is returned as a row dictionary.
        '''
        self.cursor.execute('SELECT * FROM reading WHERE id=? ORDER BY ts DESC LIMIT 1', (id,))
        row = self.cursor.fetchone()
        return dict(row) if row else {}

    def rowsForOneID(self, sensor_id, start_tm=None, end_tm=None):
        '''
        Returns a list of dictionaries, each dictionary having a 'ts' and 'val' key.  The
        rows are for a particular sensor ID, and can be further limited by a time range.
        'start_tm' and 'end_tm' are UNIX timestamps.  If either are not provided, no limit
        is imposed.  The rows are returned in timestamp order.
        '''
        sql = 'SELECT ts, val FROM reading WHERE id="%s"' % sensor_id
        if start_tm is not None:
            sql += ' AND ts>=%s' % int(start_tm)
        if end_tm is not None:
            sql += ' AND ts<=%s' % int(end_tm)
        sql += ' ORDER BY ts'

        self.cursor.execute(sql)
        return [dict(r) for r in self.cursor.fetchall()]

    def readingCount(self, startTime=0):
        """
        Returns the number of readings in the reading table inserted after the specified
        'startTime' (Unix seconds).
        """
        self.cursor.execute('SELECT COUNT(*) FROM reading WHERE ts > ?', (startTime,))
        return self.cursor.fetchone()[0]