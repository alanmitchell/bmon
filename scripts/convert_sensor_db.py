#!/usr/local/bin/python2.7
'''
Converts a BMS sensor database in the old format (id, ts, val) into the new
format where each different sensor has a dedicated Table where the table name
is the ID of the sensor.  The table format is (ts, val).
'''
import sqlite3

IN_DB = '/home/ahfc/webapps/django/bms/bmsapp/data/bms_data.sqlite'        # name of database in old format
OUT_DB = '/home/ahfc/webapps/django/bms/bmsapp_new/data/bms_data.sqlite'   # name of new database to create

conn_in = sqlite3.connect(IN_DB)
c_in = conn_in.cursor()
conn_out = sqlite3.connect(OUT_DB)
c_out = conn_out.cursor()

c_in.execute('select distinct id from reading')
ids = [rec[0] for rec in c_in.fetchall()]

for id in ids:
    print id
    c_in.execute('select ts, val from reading where id=?', (id,))
    recs = c_in.fetchall()
    c_out.execute('CREATE TABLE [%s] (ts integer primary key, val real)' % id)
    c_out.executemany('INSERT INTO [%s] VALUES (?,?)' % id, recs)
    conn_out.commit()
    
conn_in.close()
conn_out.close()
