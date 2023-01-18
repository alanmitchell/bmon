'''Terminates any main_cron processes that are older than a certain
time threshhold. Should be run with the django-extensions runscript facility:

    manage.py runscript terminate_old_cron

This script is also called from the main_cron.py script.    
'''
import getpass
import subprocess

# Hold a main_cron process must be in seconds before being terminated.
OLD_SECS = 3600

def run():
    '''Looks for main_cron processes and terminates ones that are older than one hour.
    '''
    # determine the User name that is running BMON.
    this_user = getpass.getuser()

    completed = subprocess.run(f'ps -u {this_user} -o pid,etimes,command', shell=True, text=True, check=False, stdout=subprocess.PIPE)
    for proc in completed.stdout.splitlines():
        if 'runscript main_cron' in proc:
            flds = proc.split()
            pid = flds[0].strip()
            etime = float(flds[1])
            if etime > OLD_SECS:
                print(f'Terminating: {pid}')
                subprocess.run(f'kill {pid}', shell=True, check=False)
