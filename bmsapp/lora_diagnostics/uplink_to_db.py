"""Checks for complete Things message log files and writes them
to the database.
"""
from pathlib import Path
import time

from .db_connect import get_rw_db_conn

# Determines how recent of records to keep.
DB_RETENTION = 90     # days

# tracks epoch timestamp of when the DB was last cleaned of old records.
last_cleaned = None


def check_for_complete_log_files():
    """Stores any complete uplink log files in the diagnostic database. Creates table,
    if needed. Cleans out old records periodically.
    """
    global last_cleaned
    
    try:
        conn = get_rw_db_conn()
    except:
        # more gentle error treatment; don't flood error log file.
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

    # Check to see if database needs cleaning of old records. Clean every 24 hours.
    if last_cleaned is None or (time.time() - last_cleaned) / 3600.0  > 24.0:
        conn.execute(f"DELETE FROM gateway WHERE ts < now() - INTERVAL '{DB_RETENTION} days';")
        last_cleaned = time.time()
        print("LoRa Diagnostic Database cleaned.")

    log_dir = Path(__file__).parent / "gtw-log"
    complete_log_files = list(log_dir.glob("gtw.log.*"))
    if len(complete_log_files):
        for fpath in complete_log_files:
            try:
                conn.execute(f"COPY gateway FROM '{fpath}';")
                fpath.unlink()
                
            except:
                print(f"Error processing {fpath}")
