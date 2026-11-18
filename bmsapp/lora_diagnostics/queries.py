"""Queries on the LoRa gateway diagnostic data used by BMON's web pages.

Each query runs on a connection from store.connect(), where the diagnostic
data is the view 'gateway' and the main Django SQLite database is attached as
'bmon'. The Django tables are read with plain SQL, not through Django models,
so these queries would need to change if BMON moved off SQLite.
"""
from .store import connect


def _query(sql: str):
    """Runs 'sql' and returns the result as a Pandas DataFrame. Raises an
    error if the query fails or there is no diagnostic data yet.
    """
    conn = connect(attach_bmon=True)
    try:
        return conn.sql(sql).df()
    finally:
        conn.close()


# A chain of WITH tables ending in "gtw_to_bldg", which matches each gateway_id
# to the building (or buildings) containing the sensor that the gateway hears
# with the strongest signal.
SQL_GTW_TO_BLDG = """
-- Links device EUI (root of sensor_id) to the building it's associated with
WITH eui_to_bldg AS (
    SELECT str_split(sen.sensor_id, '_')[1] AS device_eui, bldg.title AS building
    FROM bmon.bmsapp_bldgtosensor AS btos
    JOIN bmon.bmsapp_sensor AS sen
        ON btos.sensor_id = sen.id
    JOIN bmon.bmsapp_building AS bldg
        ON btos.building_id = bldg.id
),

-- There are many records with the same device EUI; combine the associated
-- buildings together into a list.
eui_to_bldgs AS (
    SELECT device_eui, string_agg(DISTINCT building, ', ' ORDER BY building) AS building_list
    FROM eui_to_bldg
    GROUP BY device_eui
),

-- The most recent 1000 records for each gateway. arg_max(..., ts, 1000) is a
-- top-N aggregate, which is several times faster here than ranking every
-- row with a window function.
recent_gateway_records AS (
    SELECT gateway_id, rec.device_eui, rec.signal_rssi
    FROM (
        SELECT
            gateway_id,
            unnest(arg_max({'device_eui': device_eui, 'signal_rssi': signal_rssi}, ts, 1000)) AS rec
        FROM gateway
        GROUP BY gateway_id
    )
),

-- For each gateway, the device with the largest signal strength, considering
-- only devices that are assigned to a building. Ties go to the lowest EUI so
-- that the result is the same on every run.
gtw_to_strongest_sensor AS (
    SELECT gateway_id, device_eui
    FROM (
        SELECT
            gateway_id,
            device_eui,
            ROW_NUMBER() OVER (
                PARTITION BY gateway_id
                ORDER BY signal_rssi DESC, device_eui
            ) AS rn
        FROM recent_gateway_records
        WHERE device_eui IN (SELECT DISTINCT device_eui FROM eui_to_bldg)
    )
    WHERE rn = 1
),

-- Bring in the building list associated with that device
gtw_to_bldg AS (
    SELECT gateway_id, building_list
    FROM gtw_to_strongest_sensor
    JOIN eui_to_bldgs
        ON gtw_to_strongest_sensor.device_eui = eui_to_bldgs.device_eui
)
"""


def inoperative_gateways(time_cutoff_hours: float):
    """Returns a DataFrame of the gateways that have not relayed a sensor
    reading in the last 'time_cutoff_hours' hours, longest-silent first.
    Columns are 'gateway_id' and 'time_since_last'.
    """
    return _query(f"""
    SELECT
        gateway_id,
        now() - max(ts) AS time_since_last
    FROM gateway
    GROUP BY gateway_id
    HAVING time_since_last > INTERVAL '{float(time_cutoff_hours)} hours'
    ORDER BY time_since_last DESC
    """)


def gateway_location():
    """Returns a DataFrame with columns 'gateway_id' and 'location', where the
    location is the building(s) of the sensor with the strongest signal that
    communicates through the gateway.
    """
    return _query(
        SQL_GTW_TO_BLDG
        + "SELECT gateway_id, building_list AS location FROM gtw_to_bldg ORDER BY gateway_id"
    )
