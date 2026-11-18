"""Captures gateway diagnostic information from Things v3 uplink messages.

Each uplink is turned into one CSV line per gateway that received it, and
those lines are appended to a rotating log file in the 'gtw-log' directory.
The log is only a short-term buffer: every 5 minutes the file rotates, and the
ingest step (see store.py) moves completed files into the Parquet store.
"""
import logging

from concurrent_log_handler import ConcurrentTimedRotatingFileHandler

from .store import LOG_DIR


def parse_uplink(msg: dict) -> list:
    """Returns one CSV line for each gateway that received the Things v3 uplink
    message 'msg'. The fields are in the order of store.COLUMNS. None of the
    values can contain a comma, so no quoting is needed.
    """
    ids = msg["end_device_ids"]
    uplink = msg["uplink_message"]

    ts = msg["received_at"]        # ISO 8601 text timestamp, UTC
    dev_eui = ids["dev_eui"]
    frame_counter = uplink["f_cnt"]
    dr = uplink["settings"]["data_rate"]["lora"]
    data_rate = f"SF{dr['spreading_factor']}BW{int(dr['bandwidth'] / 1000)}"

    # These three are stored as empty fields (NULL in the store) if absent.
    device_id = ids.get("device_id") or ""
    application_id = ids.get("application_ids", {}).get("application_id") or ""
    frm_payload = uplink.get("frm_payload") or ""     # base64 text

    lines = []
    for gtw in uplink["rx_metadata"]:
        gateway_id = gtw["gateway_ids"]["gateway_id"]
        lines.append(
            f"{ts},{dev_eui},{frame_counter},{gateway_id},{gtw['snr']},{gtw['rssi']},"
            f"{data_rate},{device_id},{application_id},{frm_payload}"
        )
    return lines


def store_things_uplink_diagnostics(msg: dict) -> dict:
    """Records the gateway diagnostics of the Things v3 uplink message 'msg'.
    """
    lines = parse_uplink(msg)
    for line in lines:
        _logger.info(line)

    return {"message": f"OK, {len(lines)} records added"}


def _make_logger():
    """Returns a logger that writes bare message text to gtw-log/gtw.log,
    starting a new file every 5 minutes. The handler is safe to use from
    multiple BMON worker processes.
    """
    logger = logging.getLogger("uplink_gateway_logger")
    logger.setLevel(logging.INFO)

    handler = ConcurrentTimedRotatingFileHandler(
        filename=LOG_DIR / "gtw.log",
        mode="a",
        when="M",
        interval=5,        # minutes
        backupCount=12,    # an hour of files, in case ingest is not running
    )
    handler.setFormatter(logging.Formatter("%(message)s"))

    # avoid duplicate handlers if this module is re-imported
    logger.handlers.clear()
    logger.addHandler(handler)
    return logger


_logger = _make_logger()
