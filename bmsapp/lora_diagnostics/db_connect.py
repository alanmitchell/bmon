"""LoRa Database connection functions.
"""
from pathlib import Path
import time

import duckdb

db_path = Path(__file__).parent / "db" / "things.db"

def get_rw_db_conn():
    """Returns a read/write connection to the diagnostic database, retrying if needed.
    Returns None if connection is unsuccessful. Increasing waits between retries, because
    longer waits are not a problem (no user interaction) for the writes that occur.
    Read/write connections will lock-out other processes, and will lock-out read-only 
    connections in the same process (all connections in the same process must be of the
    same type).
    """
    wait = 1.0     # seconds
    retries = 3
    for i in range(retries):
        try:
            conn = duckdb.connect(db_path, read_only=False)
            return conn
        except:
            if i != retries - 1:
                time.sleep(wait)
                wait *= 2.0

    return None

def get_read_only_db_conn():
    """Returns a read-only connection to the diagnostic database, retrying if needed.
    Returns None if unsuccessful. Constant wait, short retries, cuz User is waiting.
    Different processes can have simultaneous read-only connections.
    """
    wait = 0.5     # seconds
    retries = 3
    for i in range(retries):
        try:
            conn = duckdb.connect(db_path, read_only=True)
            return conn
        except:
            if i != retries - 1:
                time.sleep(wait)

    return None
