
# Execute in this namespace the file containing settings that are generally common to all
# installs of BMON.
from os.path import dirname, join, abspath
execfile(join(dirname(abspath(__file__)), 'settings_common.py'))

# If you need to override any of the settings in the 'settings_common.py' file
# do so below this point in this file.
