"""Main script for the Things API application. Receives and processes
HTTP requests. Starts a thread that stores Things message data into a
database.
"""
import logging
from pathlib import Path

from concurrent_log_handler import ConcurrentTimedRotatingFileHandler

from . import things_parser

def store_things_uplink_diagnostics(payload):
    recs = things_parser.parse_uplink_gateway_diagnostics(payload)
    for rec in recs:
        gtw_logger.info(rec)

    return {"message": f"OK, {len(recs)} records added"}

def setup_uplink_gateway_logger():
    """
    This sets up a logger that is used record gateway information for each sensor
    uplink post message. It is a timed rotating file logger. A separate process
    reads the log files and posts them to a database. Thus the log files do
    not need to be kept for a long period of time.
    """
    # Create a logger object.
    logger = logging.getLogger("uplink_gateway_logger")
    logger.setLevel(logging.INFO)  # or DEBUG, WARNING, etc.

    # Create a timed rotating file handler.
    handler = ConcurrentTimedRotatingFileHandler(
        filename=Path(__file__).parent / "gtw-log/gtw.log",
        mode="a",
        when='M',
        interval=5,       # minutes
        backupCount=12
    )

    # Define a simple format that includes *only* the raw message text.
    # No timestamps, no log level, etc.
    formatter = logging.Formatter("%(message)s")

    # Apply the formatter to the handler.
    handler.setFormatter(formatter)

    # If the logger already has handlers, remove them so we don’t add duplicates.
    if logger.hasHandlers():
        logger.handlers.clear()

    # Add the new rotating file handler to the logger.
    logger.addHandler(handler)

    return logger


# Set up the gateway uplink message logger.
gtw_logger = setup_uplink_gateway_logger()

