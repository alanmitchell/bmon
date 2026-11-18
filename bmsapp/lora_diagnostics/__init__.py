"""Gateway diagnostics for LoRaWAN sensors that report through the Things network.

How the data flows:

1. uplink_log.py - each Things uplink message is written as CSV lines (one per
   receiving gateway) to a log file that rotates every 5 minutes.
2. store.py      - ingest(), run by the main cron job, moves completed log
   files into the store: one Parquet file per day in db/gateway/.
3. queries.py    - the queries behind BMON's gateway pages.

For ad hoc analysis, connect() returns a DuckDB connection with all of the
data available as the view 'gateway'.
"""
from .uplink_log import store_things_uplink_diagnostics
from .queries import inoperative_gateways, gateway_location
from .store import connect

__all__ = [
    'store_things_uplink_diagnostics',
    'inoperative_gateways',
    'gateway_location',
    'connect',
]
