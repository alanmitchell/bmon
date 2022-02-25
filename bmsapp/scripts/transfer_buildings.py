#!/usr/bin/env python
'''Script used to transfer buildings, sensors, alerts (w/ Recipients), and dashboard items
from one BMON server to another.  Data that are *not* transferred include:
Organizations, Building Groups, Custom Report, and Periodic Scripts.

The source BMON information comes from a 'dumpdata' file that was created by executing the
command:

    python manage.py dumpdata bmsapp > <filename for data output.json>

on the source BMON Server.

Run the script with:
    transfer_buildings.py <name of dumpdata file.json>

The User can select the buildings to transfer from the file, or request that All buildings be
transferred.
'''
# %%
from audioop import add
from dataclasses import field
import os
import sys
import json
import django
from questionary import select, checkbox, Choice

# %%

# need to add the directory two above this to the Python path
# so the bmsapp package can be found
this_dir = os.path.dirname(os.path.abspath(__file__))
app_dir = os.path.abspath(os.path.join(this_dir, '../../'))
sys.path.insert(0, app_dir)

# prep the Django environment because we need access to the module
# that manipulates the Reading database.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "bmon.settings")
django.setup()

from bmsapp.models import DashboardItem, SensorGroup, Unit, Sensor, Building, BldgToSensor, \
    BuildingMode, AlertCondition, AlertRecipient, FuelRate, ElectricRate

# %%
def find_matching(model_name, field_name, field_vals):
    """Searches the input data dictionary (in_dict at the module level) 
    for records that match certain criteria.  The primary keys of the matching 
    records are returend in a list.
    The Model searched is 'model_name'. Within those objects, the 'field_name'
    is the field that tested.  That field must have a value in the list of 
    'field_vals'.  'field_vals' can also be a scalar if only one value is
    sought.
    """
    matches = []
    # Make tuple of matching values
    match_vals = tuple(field_vals) if type(field_vals) in (list, tuple) else (field_vals,)
    
    for pk, rec in in_dict[model_name].items():
        if rec[field_name] in match_vals:
            matches.append(pk)
    
    return matches

def add_object_if_missing(model, natural_key, new_rec, ignore_fields=[]):
    """Adds a new Object to a model in the destination BMON system, if that
    object does not already exist there.  Returns the object (either the new one
    or the existing one), and a boolean value indicating whether a new object
    was added.
    'model' is the Model object in the destination BMON.
    'natural_key' is the field name or tuple of field names that uniquely identify
       an object in the Model.
    'new_rec' is the dictionary of fields for the new Object.
    'ignore_fields' is a field name or tuple of field names to ignore when creating
        the new object (most likely because they are Objects, not scalar values). 
    """
    # make a dictionary of the natural key/value pairs.
    key_dict = {}
    if type(natural_key) in (list, tuple):
        for fld in natural_key:
            key_dict[fld] = new_rec[fld]
    else:
        key_dict[natural_key] = new_rec[natural_key]

    # find an object that meets the criteria
    objs = model.objects.filter(**key_dict)
    if len(objs) > 0:
        # there is an existing object with this natural key. Return it.
        # The False indicates that the object is not new.
        return objs[0], False

    else:
        # need to make a new object.  First delete fields to ignore from new
        # record.
        rec_pruned = new_rec.copy()
        del_fields = ignore_fields if type(ignore_fields) in (list, tuple) else (ignore_fields, )
        for fld in del_fields:
            rec_pruned.pop(fld)
        new_obj = model(**rec_pruned)

        # if theere were no ignored fields, save this to the database; otherwise, calling routine
        # will finish adding the ignored fields and need to save.
        if len(del_fields)==0:
            new_obj.save()

        return new_obj, True       # True indicates a new object

# %%
#fn_dump = sys.argv[2]
fn_dump = '/home/tabb99/temp/bmondump.json'
dump_list = json.load(open(fn_dump, 'r'))

# Reformat the data so that the data structure is a dictionary of dictionaries.
# First level key is the model name (all lowercase).  The value of that key is a
# dictionary mapping primary key to a model object.
in_dict = {}
for item in dump_list:
    model = item['model'].split('.')[1]
    model_dict = in_dict.get(model, {})
    model_dict[item['pk']] = item['fields']
    in_dict[model] = model_dict

# %%
# Get a dictionary of just the building objects
bldgs = in_dict['building']

# %%
#'''
choices = [
    'All',
    'Selected Buildings'
]
bldg_set = select(
    'Process which Buildings?',
    choices=choices).ask()

if bldg_set == choices[0]:
    target_bldgs = list(bldgs.keys())
else:
    # assemble a list of choices
    choices = [Choice(bldgs[pk]['title'], pk)  for pk in bldgs.keys()]
    target_bldgs = checkbox(
        'Use Space Bar to select Buildings to Transfer:',
        choices = choices
    ).ask()
#'''
#target_bldgs = [3, 5]
    
# %%
# Add all the building modes in case they are needed in the future (beyond the 
# modes that are currently being utilized)
modes = in_dict.get('buildingmode', {})
for pk in modes.keys():
    add_object_if_missing(BuildingMode, 'name', modes[pk])

# %%
# The natural key for the building-to-sensor links involves objects, so the add_object 
# routine doesn't work.  Use a more manual approach to determining existence of 
# objects.
# make a list of (building name, sensor_id, sensor group title) for the
# destination system.
link_keys = []
for obj in BldgToSensor.objects.all():
    link_keys.append( (obj.building.title, obj.sensor.sensor_id, obj.sensor_group.title) )

# Add the buildings and the related objects
# Get Electric and Fuel Rate records for easier access
electric_rates = in_dict.get('electricrate', {})
fuel_rates = in_dict.get('fuelrate', {})

# Sensors, bldg-to-sensor links, sensor groups, and units for easier access
sensors = in_dict.get('sensor', {})
bldg_to_sensors = in_dict.get('bldgtosensor', {})
sensor_groups = in_dict.get('sensorgroup', {})
units = in_dict.get('unit', {})

# %%
for bldg_pk in target_bldgs:
    bldg = bldgs[bldg_pk]
    print(f"Transferring: {bldg['title']}...")
    bldg_obj, is_new = add_object_if_missing(Building, 'title', bldg,
        ['current_mode', 'electric_rate', 'fuel_rate'])
    if is_new:
        # need to add related objects if it is a new object
        if bldg['current_mode'] is not None:
            cur_mode, _ = add_object_if_missing(BuildingMode, 'name', modes[bldg['current_mode']])
            bldg_obj.current_mode = cur_mode
        if bldg['electric_rate'] is not None:
            elec_rate, _ = add_object_if_missing(ElectricRate, 'title', electric_rates[bldg['electric_rate']])
            bldg_obj.electric_rate = elec_rate
        if bldg['fuel_rate'] is not None:
            fuel_rate, _ = add_object_if_missing(FuelRate, 'title', fuel_rates[bldg['fuel_rate']])
            bldg_obj.fuel_rate = fuel_rate
        bldg_obj.save()

    # Add the Sensors and Building-to-Sensor links associated with these buildings.
    sensor_links = find_matching('bldgtosensor', 'building', bldg_pk)
    for link_pk in sensor_links:
        link = bldg_to_sensors[link_pk]
        sensor = sensors[link['sensor']]
        sensor_obj, is_new = add_object_if_missing(Sensor, 'sensor_id', sensor, 'unit')
        if is_new:
            unit_obj, _ = add_object_if_missing(Unit, 'label', units[sensor['unit']])
            sensor_obj.unit = unit_obj
            sensor_obj.save()
        sensor_group_obj, _ = add_object_if_missing(SensorGroup, 'title', sensor_groups[link['sensor_group']])

        # only add if link does not exist
        if (bldg_obj.title, sensor_obj.sensor_id, sensor_group_obj.title) not in link_keys:
            link_pruned = link.copy()
            link_pruned.pop('building')
            link_pruned.pop('sensor')
            link_pruned.pop('sensor_group')
            link_obj = BldgToSensor(**link_pruned)
            link_obj.building = bldg_obj
            link_obj.sensor = sensor_obj
            link_obj.sensor_group = sensor_group_obj
            link_obj.save()

# %%

# --- DASHBOARD ITEMS

print('\nMaking Dashboard Items...')

# The natural key for dashboard items involves objects, so the add_object 
# routine doesn't work.  Use a more manual approach to determining existence of 
# objects.
# make a list of (building name, sensor_id, widget type) for the
# destination system. Remember that the reference to the Sensor for a DashboardItem
# is actually a reference to a Bldg-to-Sensor item.
dash_keys = []
for obj in DashboardItem.objects.all():
    dash_keys.append( (obj.building.title, obj.sensor.sensor.sensor_id, obj.widget_type) )

# Find the dashboard items related to the target building set.
dashboard_pks = find_matching('dashboarditem', 'building', target_bldgs)
for dash_pk in dashboard_pks:
    dash = in_dict['dashboarditem'][dash_pk]

    # if the dashboard doesn't exist, add it. First determine the key for this item.
    sensor_id = sensors[bldg_to_sensors[dash['sensor']]['sensor']]['sensor_id']
    dash_key = (bldgs[dash['building']]['title'], sensor_id, dash['widget_type'])
    if dash_key not in dash_keys:

        # Get the associated building object. We know this exists
        bldg_obj = Building.objects.filter(title=bldgs[dash['building']]['title'])[0]
        
        # Get sensor object, which is acutally a Building-to-Sensor Object
        b_to_s_objs = BldgToSensor.objects.filter(building__title=bldg_obj.title, sensor__sensor_id=sensor_id)
        if len(b_to_s_objs) > 0:
            # take first item
            b_to_s_obj = b_to_s_objs[0]
        else:
            # maybe not possible, but sensor does not exist, go on to next dashboard item
            continue

        dash_pruned = dash.copy()
        dash_pruned.pop('building')
        dash_pruned.pop('sensor')
        new_dash = DashboardItem(**dash_pruned)
        new_dash.building = bldg_obj
        new_dash.sensor = b_to_s_obj
        new_dash.save()

# --- ALERTS and RECIPIENTS

# %%
