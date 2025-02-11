"""Checks for complete Things message log files and writes them
to the database.
"""
from pathlib import Path

from .db_connect import get_rw_db_conn

def check_for_complete_log_files():
    """Stores any complete uplink log files in the diagnostic database.
    """
    conn = get_rw_db_conn()
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
