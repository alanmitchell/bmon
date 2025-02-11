"""Checks for complete Things message log files and writes them
to the database.
"""
from pathlib import Path

import duckdb

def check_for_complete_log_files():
    db_path = Path(__file__).parent / "db" / "things.db"
    conn = duckdb.connect(db_path)

    # Check to see if the gateway table exists
    tables = conn.execute("SHOW TABLES").fetchdf()
    if "gateway" not in tables["name"].values:
        # create the gateway table
        conn.execute("""
            CREATE TABLE gateway (
            ts TIMESTAMP,
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
