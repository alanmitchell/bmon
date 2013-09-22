'''
Class to encapsulate a BMS database.  Uses the SQLite database
'''

import os, sqlite3, time
import pandas as pd

class BMSdata:

    def __init__(self, fname):
        '''
        fname: full path to SQLite database file. If the file is not present, it will be created with
            the proper structure.
        '''

        # Open db file if it exists, or make the database if it doesn't exist.  Store
        # the connection object as an object variable.
        if os.path.exists(fname):
            self.conn = sqlite3.connect(fname)
        else:
            # no file, so make the necessary table and indexes.
            self.conn = sqlite3.connect(fname)
            self.conn.execute("CREATE TABLE reading(ts integer not null, id varchar(15) not null, val real, primary key (ts, id))")
            self.conn.execute("CREATE INDEX id_ix on reading(id)")
            self.conn.execute("CREATE INDEX ts_ix on reading(ts)")
            self.conn.commit()

        # use the SQLite Row row_factory for all Select queries
        self.conn.row_factory = sqlite3.Row

        # now create a cursor object
        self.cursor = self.conn.cursor()

    def close(self):
        self.conn.close()

    def insert_reading(self, ts, id, val):
        '''
        Inserts a record into the database and commits it.
        '''
        self.cursor.execute("INSERT INTO reading (ts, id, val) VALUES (?, ?, ?)", (ts, id, val))
        self.conn.commit()

    def last_read(self, id):
        '''
        Returns the last reading for a particular sensor.  The reading is returned as a row dictionary.
        '''
        self.cursor.execute('SELECT * FROM reading WHERE id=? ORDER BY ts DESC LIMIT 1', (id,))
        row = self.cursor.fetchone()
        return dict(row) if row else {}

    def rowsWhere(self, whereClause):
        '''
        Returns a list of row dictionaries matching the 'whereClause'.  The where clause
        can include ORDER BY and other clauses that can appear after WHERE.
        '''
        self.cursor.execute('SELECT * FROM reading WHERE ' + whereClause)
        return [dict(r) for r in self.cursor.fetchall()]

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