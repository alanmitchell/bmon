'''Moves completed LoRa gateway diagnostic log files into the Parquet store.
Normally run by main_cron every 5 minutes, but can be run by itself:

    manage.py runscript lora_diagnostics_ingest

'''
from bmsapp.lora_diagnostics import store


def run():
    '''The function executed by runscript.
    '''
    store.ingest()
