"""Checks for complete Things message log files and writes them
to the database.
"""
from pathlib import Path
import time

import duckdb

def get_db_conn():
    """Gets a connection to the diagnostic database, retrying if needed.
    """
    db_path = Path(__file__).parent / "db" / "things.db"
    wait = 1.0     # seconds
    retries = 3
    for i in range(retries):
        try:
            conn = duckdb.connect(db_path)
            return conn
        except:
            if i != retries - 1:
                time.sleep(wait)
                wait *= 2.0

    return None

def check_for_complete_log_files():
    """Stores any complete uplink log files in the diagnostic database.
    """
    conn = get_db_conn()
    if conn is None:
        print('No database connection')
        return

    # Check to see if the gateway table exists
    tables = conn.execute("SHOW TABLES").fetchdf()
    if "gateway" not in tables["name"].values:
        # create the gateway table
        conn.execute("""
            CREATE TABLE gateway (
            ts TIMESTAMPTZ,
            device_eui VARCHAR,
            frame_counter INTEGER,
            gateway_id VARCHAR,
            signal_snr FLOAT,
            signal_rssi INT2,
            data_rate VARCHAR
            )"""
        )

    log_dir = Path(__file__).parent / "gtw-log"
    complete_log_files = list(log_dir.glob("gtw.log.*"))
    if len(complete_log_files):
        for fpath in complete_log_files:
            try:
                conn.execute(f"COPY gateway FROM '{fpath}';")
                fpath.unlink()
                
            except:
                print(f"Error processing {fpath}")
