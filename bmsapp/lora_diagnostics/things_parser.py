"""Function for pulling out important diagnostic info from a Things V3
uplink message.
"""

def parse_uplink_gateway_diagnostics(things_uplink_message: dict):
    """Parses the desirable gateway diagnostic information from a Things v3 JSON 
    uplink message and returns comma-separated records for each gateway reached.
    """
    rec = things_uplink_message
    gtw_recs = []  # holds gateway records

    dev_eui = rec["end_device_ids"]["dev_eui"]
    ctr = rec["uplink_message"]["f_cnt"]              # frame counter
    ts = rec["received_at"]      # this a text ISO 8601 timestamp, UTC timezone
    dr = rec["uplink_message"]["settings"]["data_rate"]["lora"]
    data_rate = f"SF{dr['spreading_factor']}BW{int(dr['bandwidth'] / 1000)}"

    # add to list of gateway records
    for gtw in rec["uplink_message"]["rx_metadata"]:
        r = {}
        r["gtw_id"] = gtw["gateway_ids"]["gateway_id"]
        r["snr"] = gtw["snr"]
        r["rssi"] = gtw["rssi"]
        gtw_recs.append(r)

    final_recs = []
    for gtw in gtw_recs:
        r = f"{ts},{dev_eui},{ctr},{gtw['gtw_id']},{gtw['snr']},{gtw['rssi']},{data_rate}"
        final_recs.append(r)

    return final_recs

def uplink_gateway_columns():
    """Returns the column names for the data returned by "parse_uplink_gateway_info"
    """
    return [
        "ts",
        "device_eui",
        "frame_counter",
        "gateway_id",
        "signal_snr",
        "signal_rssi",
        "data_rate"
    ]
