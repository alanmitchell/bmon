"""The LoRa gateway diagnostic data store: a directory of Parquet files.

There is one file per UTC day, db/gateway/YYYY-MM-DD.parquet, each with the
columns listed in COLUMNS. There is no database file and no locking for
readers: any number of processes can query the files with DuckDB (or any other
Parquet reader) for as long as they like.

Writing happens in one place only, ingest(), which is run every 5 minutes by
the main cron job. Files are always replaced atomically, so a reader sees
either the old or the new version of a day file, never a partial one.

Stand-alone scripts can query the data with connect(). Importing anything
from the bmsapp package requires Django settings, so run such scripts with
the environment variable DJANGO_SETTINGS_MODULE=bmon.settings:

    from bmsapp.lora_diagnostics import connect
    conn = connect()
    conn.sql("SELECT count(*) FROM gateway").show()
"""
from contextlib import contextmanager
from datetime import date, datetime, timedelta, timezone
import fcntl
import os
from pathlib import Path

import duckdb

PACKAGE_DIR = Path(__file__).parent
LOG_DIR = PACKAGE_DIR / "gtw-log"              # rotating CSV log files, see uplink_log.py
GATEWAY_DIR = PACKAGE_DIR / "db" / "gateway"   # the Parquet day files
LOCK_PATH = PACKAGE_DIR / "db" / ".ingest.lock"
LEGACY_DB_PATH = PACKAGE_DIR / "db" / "things.db"   # the DuckDB file used before Parquet
DJANGO_DB_PATH = PACKAGE_DIR.parent.parent / "bmon.sqlite"

# Days of data to keep.
RETENTION_DAYS = 90

# Column names and DuckDB types of the gateway data, in CSV log file order.
# Log lines written before the last three columns existed have only 7 fields;
# those columns must stay at the end so such lines load with NULLs.
COLUMNS = {
    "ts": "TIMESTAMPTZ",           # when the Things network received the uplink
    "device_eui": "VARCHAR",
    "frame_counter": "INTEGER",
    "gateway_id": "VARCHAR",
    "signal_snr": "FLOAT",
    "signal_rssi": "SMALLINT",
    "data_rate": "VARCHAR",        # e.g. SF7BW125
    "device_id": "VARCHAR",
    "application_id": "VARCHAR",
    "frm_payload": "VARCHAR",      # base64 text, as sent by the Things network
}
LEGACY_COLUMN_COUNT = 7


# ------------------------------ Reading ------------------------------

def connect(attach_bmon: bool = False):
    """Returns an in-memory DuckDB connection in which the view 'gateway'
    holds all of the gateway diagnostic data. If 'attach_bmon' is True, the
    main Django SQLite database is also attached, read-only, as 'bmon'.
    Raises an error if there is no data yet.
    """
    conn = duckdb.connect()
    conn.execute(
        f"CREATE VIEW gateway AS SELECT * FROM read_parquet('{GATEWAY_DIR}/*.parquet')"
    )
    if attach_bmon:
        conn.execute(f"ATTACH '{DJANGO_DB_PATH}' AS bmon (TYPE sqlite, READ_ONLY)")
    return conn


# ------------------------------ Writing ------------------------------

def ingest():
    """Moves completed uplink log files into the Parquet store and deletes
    day files older than the retention period. On the first run after an
    upgrade it also converts the old DuckDB database to Parquet. Does nothing
    if another ingest is already running.
    """
    with _ingest_lock() as acquired:
        if not acquired:
            return

        GATEWAY_DIR.mkdir(parents=True, exist_ok=True)
        if LEGACY_DB_PATH.exists():
            migrate_legacy_db()

        log_files = sorted(LOG_DIR.glob("gtw.log.*"))
        if log_files:
            _load_log_files(log_files)

        purge_old_files()


def purge_old_files():
    """Deletes day files that are older than the retention period.
    """
    cutoff = datetime.now(timezone.utc).date() - timedelta(days=RETENTION_DAYS)
    for path in GATEWAY_DIR.glob("*.parquet"):
        try:
            file_day = date.fromisoformat(path.stem)
        except ValueError:
            continue      # not one of our day files
        if file_day < cutoff:
            path.unlink()


def migrate_legacy_db():
    """Converts the DuckDB database used before the Parquet store into day
    files, then renames it to 'things.db.migrated' so this runs only once. The
    renamed file is not used again and can be deleted by hand. Rows outside
    the retention period are not converted. Safe to re-run if interrupted.
    """
    conn = duckdb.connect(str(LEGACY_DB_PATH), read_only=True)
    try:
        conn.execute("SET TimeZone = 'UTC'")
        has_table = conn.execute(
            "SELECT count(*) FROM information_schema.tables WHERE table_name = 'gateway'"
        ).fetchone()[0]
        if has_table:
            new_cols = list(COLUMNS)[LEGACY_COLUMN_COUNT:]
            null_cols = ", ".join(f"NULL::{COLUMNS[c]} AS {c}" for c in new_cols)
            source = f"(SELECT *, {null_cols} FROM gateway)"
            cutoff = datetime.now(timezone.utc).date() - timedelta(days=RETENTION_DAYS)
            days = conn.execute(
                "SELECT DISTINCT ts::DATE FROM gateway WHERE ts::DATE >= ? ORDER BY 1", [cutoff]
            ).fetchall()
            for (day,) in days:
                _write_day_file(conn, day, f"SELECT * FROM {source} WHERE {_day_filter(day)}")
    finally:
        conn.close()

    LEGACY_DB_PATH.rename(LEGACY_DB_PATH.with_name(LEGACY_DB_PATH.name + ".migrated"))
    print("LoRa Diagnostic database converted to Parquet files.")


def _load_log_files(log_files):
    """Adds the records in the CSV 'log_files' to the day files they belong
    to, then deletes the log files. A log file that cannot be read is moved to
    the 'bad' subdirectory so it does not block the others.
    """
    conn = duckdb.connect()
    try:
        conn.execute("SET TimeZone = 'UTC'")
        col_defs = ", ".join(f"{name} {dtype}" for name, dtype in COLUMNS.items())
        conn.execute(f"CREATE TABLE incoming ({col_defs})")

        loaded = []
        for path in log_files:
            try:
                # null_padding fills the columns missing from 7-field lines.
                # auto_detect must be off: DuckDB's format sniffer rejects a
                # file that mixes 7-field and 10-field lines.
                conn.execute(
                    "INSERT INTO incoming SELECT * FROM read_csv(?, auto_detect=false, "
                    "header=false, delim=',', quote='', escape='', columns=?, "
                    "null_padding=true)",
                    [str(path), COLUMNS],
                )
                loaded.append(path)
            except Exception as e:
                reason = str(e).splitlines()[0]      # DuckDB's full message is very long
                print(f"Error reading LoRa gateway log {path.name}: {reason}")
                bad_dir = LOG_DIR / "bad"
                bad_dir.mkdir(exist_ok=True)
                path.rename(bad_dir / path.name)

        days = conn.execute(
            "SELECT DISTINCT ts::DATE FROM incoming WHERE ts IS NOT NULL ORDER BY 1"
        ).fetchall()
        for (day,) in days:
            sql = f"SELECT * FROM incoming WHERE {_day_filter(day)}"
            day_file = GATEWAY_DIR / f"{day}.parquet"
            if day_file.exists():
                sql += f" UNION ALL SELECT * FROM read_parquet('{day_file}')"
            # DISTINCT means that reloading a log file (e.g. after a crash
            # between writing the day file and deleting the log) adds nothing.
            _write_day_file(conn, day, f"SELECT DISTINCT * FROM ({sql})")
    finally:
        conn.close()

    # Only now is it safe to drop the log files.
    for path in loaded:
        path.unlink()


def _day_filter(day: date) -> str:
    """SQL condition selecting the rows whose 'ts' falls on the UTC date 'day'.
    Written as a range on 'ts' so DuckDB can skip data outside the day.
    """
    return (
        f"ts >= TIMESTAMPTZ '{day} 00:00:00+00' "
        f"AND ts < TIMESTAMPTZ '{day + timedelta(days=1)} 00:00:00+00'"
    )


def _write_day_file(conn, day: date, select_sql: str):
    """Writes the rows returned by 'select_sql' as the Parquet file for 'day',
    atomically replacing any existing file.
    """
    final_path = GATEWAY_DIR / f"{day}.parquet"
    tmp_path = GATEWAY_DIR / f"{day}.parquet.tmp"     # not matched by '*.parquet'
    conn.execute(
        f"COPY ({select_sql} ORDER BY ts) TO '{tmp_path}' (FORMAT parquet, COMPRESSION zstd)"
    )
    os.replace(tmp_path, final_path)


@contextmanager
def _ingest_lock():
    """Context manager yielding True if this process obtained the exclusive
    ingest lock, False if another process holds it.
    """
    LOCK_PATH.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(LOCK_PATH, os.O_CREAT | os.O_RDWR)
    try:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            yield False
            return
        yield True
    finally:
        os.close(fd)      # also releases the lock
