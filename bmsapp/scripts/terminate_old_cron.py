'''Terminates any main_cron processes that are older than a certain
time threshhold. Should be run with the django-extensions runscript facility:

    manage.py runscript terminate_old_cron

This script is also called from the main_cron.py script.    
'''
import time
import getpass
import psutil

# Hold a main_cron process must be in seconds before being terminated.
OLD_SECS = 3600

def run():
    '''Looks for main_cron processes and terminates ones that are older than one hour.
    '''
    # determine the User name that is running BMON.
    this_user = getpass.getuser()

    # A list of all the old processes to terminate.
    to_terminate = []

    for p in psutil.process_iter(['username']):
        if p.info['username'] == this_user:
            # Check all the pieces of the command (past the interpreter command in the first
            # index) to see if the "main_cron" process is part of the name.
            for fld in p.cmdline()[1:]:
                if 'main_cron' in fld:
                    if time.time() - p.create_time() > OLD_SECS:
                        to_terminate.append(p)
                    break
    for p in to_terminate:
        print(f"Terminating: {' '.join(p.cmdline())}")
        p.terminate()
    _, alive = psutil.wait_procs(to_terminate, timeout=3)
    for p in alive:
        p.kill()
