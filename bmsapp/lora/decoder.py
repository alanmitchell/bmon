"""Module that decodes a LoRaWAN HTTP Integration payload into a field/value sensor
reading dictionary for certain supported sensor types.
"""
from typing import Dict, Any
import base64

from dateutil.parser import parse

from . import decode_elsys
from . import decode_dragino

def decode(
        integration_payload: Dict[str, Any],
        flatten_value_lists=True,
        raw_payload_priority=True,
    ) -> Dict[str, float]:
    """ Returns a dictionary of information derived from the payload sent by 
    a Things Network HTTP Integration.  Some general data about the message is included
    (e.g. Unix timestamp) but a full list of the sensor values encoded in the payload are returned
    in the 'fields' key of the dictionary. These value are pulled from the 'payload_fields' key of
    the integration_payload (if present) or by decoding the raw_payload.  The 'raw_payload_priority' parameter 
    determines which source has priority. Only sensor values from the following sensors can currently be
    decoded from the raw payload:
        All Elsys sensors
        Dragino LHT65, LWL01, LDDS20, LDDS75 sensors.
           Also, a special decoding of the LT22222 sensor for boat monitoring is included.
    
    Function Parameters are:
    'integration_payload': the data payload that is sent by a Things Network HTTP integration, 
        in Python dictionary format.
    'flatten_value_lists': some sensors, including the Elsys ELT-2, decode multiple sensor channels 
        into a list of values, for example multiple external temperature channels.  If this parameter
        is True (the default), those lists are flattened into separate sensor values by appending
        the list index to the sensor name.
    'raw_payload_priority': If True (the default), an attempt will be made first to decode the raw payload; if that
        fails and there is a 'payload_fields' key in the integration post, those values will be used.
    """

    # Determine the Things Stack version number, as the integration payload formats
    # are different between V2 and V3.
    if 'dev_id' in integration_payload:
        # Version 2 payload
        # Go here to learn about the format of an HTTP Integration Uplink coming from the Things
        # network:  https://www.thethingsnetwork.org/docs/applications/http/
        device_id = integration_payload['dev_id']
        device_eui = integration_payload['hardware_serial']
        payload = base64.b64decode(integration_payload['payload_raw'])  # is a list of bytes now

        # Make UNIX timestamp for the record
        ts = parse(integration_payload['metadata']['time']).timestamp()
        
        # Extract the strongest SNR across the gateways that received the transmission.
        snrs = [gtw['snr'] for gtw in integration_payload['metadata']['gateways']]
        snr = max(snrs)

        # get payload fields if they are present
        payload_fields = integration_payload.get('payload_fields', {})

        # get port and frame counter
        port = integration_payload['port']
        frame_counter = integration_payload['counter']

    elif 'end_device_ids' in integration_payload:
        # Version 3 payload
        # For format info, see:  https://www.thethingsindustries.com/docs/reference/data-formats/
        device_id = integration_payload['end_device_ids']['device_id']
        device_eui = integration_payload['end_device_ids']['dev_eui']
        msg = integration_payload['uplink_message']  # shortcut to uplink message
        payload = base64.b64decode(msg['frm_payload'])  # is a list of bytes now

        # Make UNIX timestamp for the record
        ts = parse(msg['received_at']).timestamp()
        
        # Extract the strongest SNR across the gateways that received the transmission.
        snrs = [gtw['snr'] for gtw in msg['rx_metadata']]
        snr = max(snrs)

        # get payload fields if they are present
        payload_fields = msg.get('decoded_payload', {})

        # get port and frame counter
        port = msg['f_port']
        frame_counter = msg['f_cnt']

    else:
        # Unrecognized payload.  Return results with no fields.
        return {'fields': {}}

    # the dictionary that will hold the decoded results.  the 'fields' key will be added later.
    results = {
        'device_eui': device_eui,
        'ts': ts,
    }

    fields = {}      # default to no field data
    if raw_payload_priority or len(payload_fields) == 0:
        try:
            # dispatch to the right decoding function based on characters in the device_id.
            # if device_id contains "lht65" anywhere in it, use the lht65 decoder
            # if device_id starts with "ers" or "elsys" or "elt", use the elsys decoder
            dev_id_lwr = device_id.lower()    # get variable for lower case device ID
            if 'lht65' in dev_id_lwr:
                # only messages on Port 2 are sensor readings (although haven't yet seen 
                # any other types of messages from this sensor)
                if port == 2:
                    fields = decode_dragino.decode_lht65(payload)
            elif dev_id_lwr.startswith('lwl01'):
                fields = decode_dragino.decode_lwl01(payload)
            elif dev_id_lwr.startswith('elsys') or (dev_id_lwr[:3] in ('ers', 'elt')):
                # only messages on Port 5 are sensor readings
                if port == 5:
                    fields = decode_elsys.decode(payload)
            elif dev_id_lwr.startswith('boat-lt2'):
                if port == 2:
                    fields = decode_dragino.decode_boat_lt2(payload)
            elif dev_id_lwr.startswith('ldds'):
                fields = decode_dragino.decode_ldds(payload)

            # some decoders will give a list of values back for one field.  If requested, convert 
            # these into multiple fields with an underscore index at end of field name.
            if flatten_value_lists:
                flat_fields = {}
                fields_to_delete = []
                for k, v in fields.items():
                    if type(v) == list:
                        fields_to_delete.append(k)
                        for ix, val in enumerate(v):
                            flat_fields[f'{k}_{ix}'] = val
                for k in fields_to_delete:
                    del fields[k]     # remove that item cuz will add individual elements
                fields.update(flat_fields)
        except:
            # Failed at decoding raw payload.  Go on to see if there might be values in 
            # the payload_fields element.
            pass

    if len(fields) == 0 and len(payload_fields) > 0:
        # get sensor data from already-decoded payload_fields
        EXCLUDE_THINGS_FIELDS = ('event', )    # fields not to include
        fields = payload_fields.copy()
        for ky in EXCLUDE_THINGS_FIELDS:
            fields.pop(ky, None)      # deletes element without an error if not there

    # Add the SNR field on every 4th frame
    if frame_counter % 5 == 0:
        fields['snr'] = snr

    # Delete the battery voltage (if present) except every 10th frame
    if frame_counter % 10 != 0:
        fields.pop('vdd', None)

    # Add these fields to the results dictionary
    results['fields'] = fields

    return results

def test():
    from pprint import pprint
    recs = [
        {"end_device_ids":{"device_id":"eltlite-scott-6632","application_ids":{"application_id":"an-bmon"},"dev_eui":"A81758FFFE056632","join_eui":"0000000000000001","dev_addr":"260C1BDB"},"correlation_ids":["as:up:01EZ5JR80C2BJBCZEAHC7QXYDV","gs:conn:01EZ5JPNH4JYBTWNV9VXXXXW69","gs:up:host:01EZ5JPNNRZD4QG5949ANFAF1Y","gs:uplink:01EZ5JR7RKKFWF4ED7AAQY02ZG","ns:uplink:01EZ5JR7RPA1NPR0711ZYYFVTQ","rpc:/ttn.lorawan.v3.GsNs/HandleUplink:01EZ5JR7RP8M42R27042B7MV3Y","rpc:/ttn.lorawan.v3.NsAs/HandleUplink:01EZ5JR7Z6600AHAS3P4VNYAVQ"],"received_at":"2021-02-22T19:16:42.697091883Z","uplink_message":{"session_key_id":"AXfGPKt+rH3iyBcL2G2tFg==","f_port":5,"f_cnt":92,"frm_payload":"Bw4kCAGO","decoded_payload":{},"decoded_payload_warnings":[],"rx_metadata":[{"gateway_ids":{"gateway_id":"scott-a840411ed9004150","eui":"A840411ED9004150"},"timestamp":4213093213,"rssi":-68,"channel_rssi":-68,"snr":13.5,"uplink_token":"CiQKIgoWc2NvdHQtYTg0MDQxMWVkOTAwNDE1MBIIqEBBHtkAQVAQ3eb62A8aDAiahtCBBhCIx+e4ASDIxrL/zno=","channel_index":3},{"gateway_ids":{"gateway_id":"packetbroker"},"packet_broker":{"message_id":"01EZ5JR7TMXXMGMYHE54B5ZBSD","forwarder_net_id":"000013","forwarder_tenant_id":"ttn","forwarder_cluster_id":"ttn-v2-us-west","home_network_net_id":"000013","home_network_tenant_id":"ttn","home_network_cluster_id":"ttn-nam1","hops":[{"received_at":"2021-02-22T19:16:42.452874367Z","sender_address":"51.143.19.11","receiver_name":"router-dataplane-76fc4fb9fd-9fslm","receiver_agent":"pbdataplane/1.2.1 go/1.15.8 linux/amd64"},{"received_at":"2021-02-22T19:16:42.474150795Z","sender_name":"router-dataplane-76fc4fb9fd-9fslm","sender_address":"kafkapb://router?topic=forwarder_uplink","receiver_name":"router-5d588c46f9-nnrrv","receiver_agent":"pbrouter/1.2.1 go/1.15.8 linux/amd64"},{"received_at":"2021-02-22T19:16:42.486565571Z","sender_name":"router-5d588c46f9-nnrrv","sender_address":"kafkapb://ttn-nam1?topic=deliver_000013.ttn.ttn-nam1_uplink","receiver_name":"router-dataplane-76fc4fb9fd-9fslm","receiver_agent":"pbdataplane/1.2.1 go/1.15.8 linux/amd64"}]},"time":"2021-02-22T19:16:42.347974Z","rssi":-59,"channel_rssi":-59,"snr":9.8,"uplink_token":"eyJnIjoiWlhsS2FHSkhZMmxQYVVwQ1RWUkpORkl3VGs1VE1XTnBURU5LYkdKdFRXbFBhVXBDVFZSSk5GSXdUazVKYVhkcFlWaFphVTlwU2t4VlZGSldVakpLV2xKSGNGVldWMG8yV2tkb1dFbHBkMmxrUjBadVNXcHZhVmRHWkc5VmFscDRZMGN4ZG1GSE9VbFVXRnBZVVd4a1YySlVRa1ZrZVVvNUxtUTNia3d4ZUVGQlN6Vm9VRXBVWDFaS2IyRjNVWGN1VFhaQ04xUjRlbXhhU0RaTE5HbFJiUzVRY3pCVlgxWnBSVFJvTFdaSFVHaGtRV1ZqUXpac2MwZDBiVkV6Y0ZFMlMzQjRXbFYwTW5sUGRGOTZTRVZTUzJGalZpMW5WMWt3ZVVkTFZFNVdRbnBLVTE5MmFYZE9XbGN4Vm1Kb1owOVJjalpPZEV0ZlgxZE5SbE52UjBkSVJFVm1WalpHZGxkalRHOVJVblE1WTJwNFEyVnZVVUl5U0RORmVIaEdhR3BhUjAwMWMwZENTVUZRUnpGVmFHOUZNWEJyWkRoYWRrbHBSRmQ1WkhSa1lYVjRWR2RNT1ZKd1FrODNZM05oTGxBNGVrcFpVak56VGxjek1sOVpYMVY1TFdwVlgxRT0iLCJhIjp7ImZuaWQiOiIwMDAwMTMiLCJmdGlkIjoidHRuIiwiZmNpZCI6InR0bi12Mi11cy13ZXN0In19"}],"settings":{"data_rate":{"lora":{"bandwidth":125000,"spreading_factor":7}},"data_rate_index":3,"coding_rate":"4/5","frequency":"904500000","timestamp":4213093213},"received_at":"2021-02-22T19:16:42.390609031Z","consumed_airtime":"0.061696s"}},
        {"end_device_ids":{"device_id":"eltlite-scott-6632","application_ids":{"application_id":"an-bmon"},"dev_eui":"A81758FFFE056632","join_eui":"0000000000000001","dev_addr":"260C1BDB"},"correlation_ids":["as:up:01EZ5SKYWPRZAZ1S9BMGJF977F","gs:conn:01EZ5SJD13PT9FD1HHCXEMSTPQ","gs:up:host:01EZ5SJD5WQC1K0YN010PKA8QJ","gs:uplink:01EZ5SKYN54DF0934H190QE3Q8","ns:uplink:01EZ5SKYN802YKRT7SD6WHRKRQ","rpc:/ttn.lorawan.v3.GsNs/HandleUplink:01EZ5SKYN8CC0HYWTDWBNGEVXR","rpc:/ttn.lorawan.v3.NsAs/HandleUplink:01EZ5SKYW3JKVM8WVF7ZPKZWN1"],"received_at":"2021-02-22T21:16:42.291696385Z","uplink_message":{"session_key_id":"AXfGPKt+rH3iyBcL2G2tFg==","f_port":5,"f_cnt":100,"frm_payload":"Bw4kCAGO","decoded_payload":{},"decoded_payload_warnings":[],"rx_metadata":[{"gateway_ids":{"gateway_id":"scott-a840411ed9004150","eui":"A840411ED9004150"},"timestamp":2822794225,"rssi":-65,"channel_rssi":-65,"snr":13.5,"uplink_token":"CiQKIgoWc2NvdHQtYTg0MDQxMWVkOTAwNDE1MBIIqEBBHtkAQVAQ8deBwgoaCwi6vtCBBhCW2J0KIOjKlt2TUg==","channel_index":4}],"settings":{"data_rate":{"lora":{"bandwidth":125000,"spreading_factor":7}},"data_rate_index":3,"coding_rate":"4/5","frequency":"904700000","timestamp":2822794225},"received_at":"2021-02-22T21:16:42.024314443Z","consumed_airtime":"0.061696s"}},
        {"end_device_ids":{"device_id":"eltlite-scott-6632","application_ids":{"application_id":"an-bmon"},"dev_eui":"A81758FFFE056632","join_eui":"0000000000000001","dev_addr":"260C1BDB"},"correlation_ids":["as:up:01EZ5CQZY9W8MM3JBYWWW0JKC0","gs:conn:01EZ5CPCY5GSFAFEA3P5MV2ADM","gs:up:host:01EZ5CPD2S4K9QK0DMX5ABX2K4","gs:uplink:01EZ5CQZQ1KT66K3B37YJCD2S4","ns:uplink:01EZ5CQZQ37CWVQPKP5DQ4RTYX","rpc:/ttn.lorawan.v3.GsNs/HandleUplink:01EZ5CQZQ35JW2BGHXADFQDGW2","rpc:/ttn.lorawan.v3.NsAs/HandleUplink:01EZ5CQZXH24RWHXGTAEGN3GWX"],"received_at":"2021-02-22T17:31:42.940570916Z","uplink_message":{"session_key_id":"AXfGPKt+rH3iyBcL2G2tFg==","f_port":5,"f_cnt":85,"frm_payload":"CAGP","decoded_payload":{},"decoded_payload_warnings":[],"rx_metadata":[{"gateway_ids":{"gateway_id":"scott-a840411ed9004150","eui":"A840411ED9004150"},"timestamp":2208369835,"rssi":-68,"channel_rssi":-68,"snr":13.2,"uplink_token":"CiQKIgoWc2NvdHQtYTg0MDQxMWVkOTAwNDE1MBIIqEBBHtkAQVAQq5mEnQgaDAj+1M+BBhCCysLIAiD49+XookA="}],"settings":{"data_rate":{"lora":{"bandwidth":125000,"spreading_factor":7}},"data_rate_index":3,"coding_rate":"4/5","frequency":"903900000","timestamp":2208369835},"received_at":"2021-02-22T17:31:42.691617631Z","consumed_airtime":"0.056576s"}},
        {"app_id":"an-dragino","dev_id":"lht65-a84041000181c74e","hardware_serial":"A84041000181C74E","port":2,"counter":33041,"payload_raw":"yxH5YAKWAfl8f/8=","payload_fields":{"bat_v":2.833,"humidity":"66.2","temp_ext":"1.98","temp_int":"1.47"},"metadata":{"time":"2020-10-30T02:35:43.883078268Z","frequency":904.7,"modulation":"LORA","data_rate":"SF7BW125","coding_rate":"4/5","gateways":[{"gtw_id":"eui-a84041ffff1ee2b4","timestamp":3580480955,"time":"2020-10-30T02:35:43.828704Z","channel":4,"rssi":-90,"snr":8,"rf_chain":0}]},"downlink_url":"https://integrations.thethingsnetwork.org/ttn-us-west/api/v2/down/an-dragino/lora-signal?key=ttn-account-v2.vL5tZaRYIpvsQiQb8Iy48z6u0hqi3BIIaCS8yubFMgU"},
        {"app_id":"sig-strength","dev_id":"elt-a81758fffe0523db","hardware_serial":"A81758FFFE0523DB","port":5,"counter":165,"payload_raw":"Bw4uDQE=","metadata":{"time":"2020-11-08T18:50:21.145287118Z","frequency":904.7,"modulation":"LORA","data_rate":"SF9BW125","coding_rate":"4/5","gateways":[{"gtw_id":"eui-58a0cbfffe8015fd","timestamp":1861174284,"time":"2020-11-08T18:50:21.086786985Z","channel":0,"rssi":-51,"snr":9.25,"rf_chain":0},{"gtw_id":"eui-a84041ffff1ee2b4","timestamp":471103348,"time":"2020-11-08T18:50:21.099979Z","channel":4,"rssi":-53,"snr":11,"rf_chain":0}]},"downlink_url":"https://integrations.thethingsnetwork.org/ttn-us-west/api/v2/down/sig-strength/lora-signal?key=ttn-account-v2.sgTyWsa1SlDoilFxQU6Q7TAWL80RhMYrM1dajv7Ej8k"},    
        {"app_id":"sig-strength","dev_id":"elt-a81758fffe0523db","hardware_serial":"A81758FFFE0523DB","port":5,"counter":100,"payload_raw":"AQDiAikEACcFBgYDCAcNYhkAARn//w==","metadata":{"time":"2020-11-08T18:50:21.145287118Z","frequency":904.7,"modulation":"LORA","data_rate":"SF9BW125","coding_rate":"4/5","gateways":[{"gtw_id":"eui-58a0cbfffe8015fd","timestamp":1861174284,"time":"2020-11-08T18:50:21.086786985Z","channel":0,"rssi":-51,"snr":9.25,"rf_chain":0},{"gtw_id":"eui-a84041ffff1ee2b4","timestamp":471103348,"time":"2020-11-08T18:50:21.099979Z","channel":4,"rssi":-53,"snr":11,"rf_chain":0}]},"downlink_url":"https://integrations.thethingsnetwork.org/ttn-us-west/api/v2/down/sig-strength/lora-signal?key=ttn-account-v2.sgTyWsa1SlDoilFxQU6Q7TAWL80RhMYrM1dajv7Ej8k"},    
    ]
    for rec in recs:
        pprint(decode(rec))

    pprint(decode(recs[-1], flatten_value_lists=False))

if __name__ == '__main__':
    # To run this without import error, need to run "python -m lora.decoder" from the 
    # bmsapp directory.
    test()
