"""Initialization of the lora_diagnostics package.
"""
import time
import threading
from pathlib import Path
import fcntl
import os

from . import uplink_to_db

# bring the key functions into the main package namespace.
from .main import store_things_uplink_diagnostics

# symbols available when someone executes: from lora_diagnostics import *
__all__ = ['store_things_uplink_diagnostics']


# ----------------------------------------

# code to start a thread that watches for complete log files and then stores
# them in the LoRa diagnostic database.

def periodically_write_to_db():
    """Start a thread to check whether there are Things message log files 
    ready to be written to the database
    """
    while True:
        try:
            uplink_to_db.check_for_complete_log_files()
            time.sleep(30)    # check every 30 seconds
        except Exception as e:
            print(f"An error occurred: {e}")
            time.sleep(10)

# start a thread to periodically check for complete Things message log 
# files that need to be written to the database.
# But, we want only one thread to be started across all the possible BMON workers.
# Use a file locking approach to enfore this.

# make a lock file in this directory.
lock_file_path = Path(__file__).parent / "db" / ".thingsdb.lock"
fd = os.open(lock_file_path, os.O_CREAT | os.O_RDWR)

try:
    # Try to acquire an exclusive non-blocking lock.
    # If the lock is already held by another process, this will raise BlockingIOError.
    fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    thread = threading.Thread(target=periodically_write_to_db, daemon=True)
    thread.start()
except:
    pass

