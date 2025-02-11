"""SQL statements that operate on the LoRa Diagnostic database.
"""
from .db_connect import get_rw_db_conn

# The function below that deletes old records uses this to determine
# how recent to keep.
DB_RETENTION = 90     # days

def delete_old_records():
    """Deletes old records in the database.
    """

    # get database connection. Will raise an error if unsuccessful.
    conn = get_rw_db_conn()

    conn.execute(f"DELETE FROM gateway WHERE ts < now() - INTERVAL '{DB_RETENTION} days';")

