"""SQL statements that operate on the LoRa Diagnostic database.

These queries access the main Django SQLite database, without using
Django's model paradigm. If BMON changes to a different type of Django
database, the queries will need to be changed, and perhaps converted to
using the Django model paradigm to make DataFrames, which are then 
queried directly by DuckDB.
"""
from bmsapp.models import path_to_django_db
from .db_connect import get_read_only_db_conn

def ro_query(sql):
    """Runs a read-only query on the diagnostic database and returns
    the results as a Pandas DataFrame. Will raise a Connection error
    if no connection possible.  Attaches the main Django database as "bmon" and
    makes it the current database.
    """
    with get_read_only_db_conn() as conn:
        conn.sql(f"ATTACH '{path_to_django_db()}' AS bmon (TYPE sqlite)")
        conn.sql("USE bmon")
        return conn.sql(sql).df()

# This query makes a With table available that has gateway_id matched
# to a building (or buildings) holding the strongest signal sensor seen
# by that gateway. The With table name is "gtw_to_bldg".
# This query assumes the main Django database is attached as "bmon" and
# has been set to current use.
sql_gtw_to_bldg = """
WITH eui_to_bldg AS (
    SELECT str_split(sen.sensor_id, '_')[1] AS device_eui, bldg.title as building
    FROM bmsapp_bldgtosensor as btos
    JOIN bmsapp_sensor as sen
        ON btos.sensor_id = sen.id
    JOIN bmsapp_building as bldg
        ON btos.building_id = bldg.id
),

eui_to_bldgs AS (
    SELECT device_eui, string_agg(DISTINCT building, ', ') AS building_list
    FROM eui_to_bldg
    GROUP BY device_eui    
),

gtw_to_sensor AS (
SELECT gateway_id, device_eui, signal_rssi
FROM (
    SELECT
        gateway_id,
        device_eui,
        signal_rssi,
        ROW_NUMBER() OVER (PARTITION BY gateway_id ORDER BY signal_rssi DESC) AS rn
    FROM things.gateway
    WHERE ts > now() - INTERVAL '14 days'
        AND device_eui IN (SELECT DISTINCT device_eui FROM eui_to_bldg)
)
WHERE rn = 1
),

gtw_to_bldg AS (
SELECT gateway_id, building_list
FROM gtw_to_sensor
JOIN eui_to_bldgs
    ON gtw_to_sensor.device_eui = eui_to_bldgs.device_eui
)
"""

def inoperative_gateways(time_cutoff_hours: float):
    """Returns a DataFrame of all the gateways that have not reported a
    sensor reading in the last 'time_cutoff_hours' hours. Gateway location,
    the time since last report, and the gateway ID are columns in the DataFrame.
    """
    df = ro_query(sql_gtw_to_bldg + f"""
    SELECT 
        building_list as location, 
        now() - max(ts) AS time_since_last, 
        things.gateway.gateway_id 
    FROM things.gateway
    LEFT JOIN gtw_to_bldg
        ON things.gateway.gateway_id =  gtw_to_bldg.gateway_id
    GROUP BY things.gateway.gateway_id, location
    HAVING time_since_last > INTERVAL '{time_cutoff_hours} hours'
    ORDER BY time_since_last DESC;
    """)
    return df

def gateway_location():
    """Returns a DataFrame that links gateway IDs to the location of the
    gateway based on the the sensor with the strongest signal that communicates
    through the gateway.
    """
    return ro_query(
        sql_gtw_to_bldg + "SELECT gateway_id, building_list as location FROM gtw_to_bldg"
        )
