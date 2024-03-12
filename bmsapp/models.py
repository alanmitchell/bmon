import time
import json
import logging
from django.db import models
from django.core.validators import RegexValidator
from django.conf import settings
from django.core.mail import send_mail
import requests
import bmsapp.data_util
import bmsapp.formatters
import bmsapp.schedule
from . import sms_gateways
import yaml


# Make a logger for this module
_logger = logging.getLogger('bms.' + __name__)

# Models for the BMS App

class SensorGroup(models.Model):
    '''
    A functional group that the sensor belongs to, e.g. "Weather, Snowmelt System".
    '''

    # the diplay name of the Sensor Group.
    title = models.CharField(max_length=80, unique=True)

    # A number that determines the order that Sensor Groups will be presented to the user.
    sort_order = models.IntegerField(default=999)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['sort_order']


class Unit(models.Model):
    '''
    A physical unit, e.g. "deg F", "gpm", for a sensor value.
    '''

    # the display name of the unit
    label = models.CharField("Unit Label", max_length=20, unique=True)

    # the type of physical quantity being measured, e.g. temperature, fluid flow, air flow, power
    measure_type = models.CharField("Measurement Type", max_length=30)

    def __str__(self):
        return '%s: %s' % (self.measure_type, self.label)

    class Meta:
        ordering = ['measure_type', 'label']


class Sensor(models.Model):
    '''
    One sensor or a calculated field
    '''

    # sensor ID, either from Monnit network or a user-entered ID for a calculated value
    sensor_id = models.CharField("Sensor ID, or Calculated Field ID", max_length=80, unique=True)

    # descriptive title for the sensor, shown to users
    title = models.CharField(max_length = 80)

    # the units for the sensor values
    # Does not allow no value.
    unit =  models.ForeignKey(Unit, models.SET_DEFAULT, default=1)

    # Adds in a notes field to the Current sensors page.
    notes = models.TextField("Please enter descriptive notes about the sensor.", default="No sensor notes available.")

    # Optional, Latitude of sensor location
    latitude = models.FloatField(default=None,null=True,blank=True)

    # Optional, Longitude of sensor location
    longitude = models.FloatField(default=None,null=True,blank=True)
    
    # if True, this field is a calculated field and is not directly created from a sensor.
    is_calculated = models.BooleanField("Calculated Field", default=False)

    # the name of the transform function to scale the value, if any, for a standard sensor field, or the 
    # calculation function (required) for a calculated field.  transform functions must be located in the 
    # "transforms.py" module in the "calcs" package and calculated field functions must be properly 
    # referenced in the "calc_readings.py" script in the "scripts" directory.
    tran_calc_function = models.CharField("Transform or Calculated Field Function Name", max_length=80, blank=True)

    # the function parameters, if any, for the transform or calculation function above.  parameters are 
    # entered in YAML format.
    function_parameters = models.TextField("Function Parameters in YAML form", blank=True)

    # Calculation order.  If this particular calculated field depends on the completion of other calculated fields
    # first, make sure the calculation_order for this field is higher than the fields it depends on.
    calculation_order = models.IntegerField(default=0)

    # the name of the formatting function for the value, if any.
    # Formatting functions must be located in the "formatters.py" module.
    formatting_function = models.CharField("Formatting Function Name", max_length=50, blank=True)

    # Additional Descriptive Properties to include in the key_properties function.
    # These are given higer priority over the other fields so can be used to override 
    # other field values.
    other_properties = models.TextField("Additional Properties to include when exporting data. YAML form, e.g. room: telecom closet", help_text="One property per line.  Name of Property, a colon, a space, and then the property value.", blank=True)

    def __str__(self):
        return self.sensor_id + ": " + self.title

    class Meta:
        ordering = ['sensor_id']

    def last_read(self, reading_db, read_count=1):
        '''If 'read_count' is 1, returns the last reading from the sensor as a dictionary
        with 'ts' and 'val' keys. Returns None if there have been no readings.
        If 'read_count' is more than 1, returns a list 'read_count' readings (if available),
        each reading as a dictionary.
        'reading_db' is a sensor reading database, an instance of bmsapp.readingdb.bmsdata.BMSdata.
        '''
        return reading_db.last_read(self.sensor_id, read_count)

    def format_func(self):
        '''Returns a function suitable for formatting a value from this sensor.
        If 'formatting_function' is present, that function is looked up and returned,
        otherwise a generic formatting function that displays 3 significant digits is
        returned.
        '''
        return getattr(bmsapp.formatters,
                       self.formatting_function.strip(),
                       bmsapp.data_util.formatCurVal)

    def is_active(self, reading_db):
        '''Returns True if the sensor has last posted within the sensor
        activity interval specified in the settings file.  'reading_db' is a sensor reading
        database, an instance of bmsapp.readingdb.bmsdata.BMSdata.
        '''
        last_read = self.last_read(reading_db)
        if last_read is not None:
            # get inactivity setting from settings file
            inactivity_hrs = getattr(settings, 'BMSAPP_SENSOR_INACTIVITY', 2.0)
            last_post_hrs = (time.time() - last_read['ts']) / 3600.0
            return (last_post_hrs <= inactivity_hrs)
        else:
            # no readings in database for this sensor
            return False

    def alerts(self, reading_db):
        '''Returns a list of alert (subject, message) tuples that are currently effective.  
        List will be empty if no alerts are occurring.
        '''
        alerts = []
        for alert_condx in AlertCondition.objects.filter(sensor__pk=self.pk):
            subject_msg = alert_condx.check_condition(reading_db)
            if subject_msg:
                alerts.append(subject_msg)
        return alerts

    def key_properties(self):
        """Returns a dictionary of important properties associated with this building.  Not all properties are 
        included.  One use is to include when exporting data.
        """
        # adding a 'sensor' qualifier to title because these props are often combined
        # with sensor properties that also have a title.
        props = {'sensor_id': self.sensor_id,
                 'sensor_title': self.title,
                 'unit': self.unit.label}
        try:
            props.update( yaml.load(self.other_properties, Loader=yaml.FullLoader) )
        except:
            # ignore errors
            pass
        
        return props


class BuildingMode(models.Model):
    '''A state or mode that the building could be in, such as Winter, Summer, Vacant.
    '''

    # name of the mode
    name = models.CharField("Mode Name", max_length=50)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']

class ElectricRate(models.Model):
    """Defines an electric rate schedule.
    """
    # Name of the Rate Schedule
    title = models.CharField(max_length=80, unique=True)

    # Determines the order that the Rate Schedule will be presented in the UI
    sort_order = models.IntegerField(default=999)

    # Monthly fixed customer charge.
    customer_charge = models.FloatField(
        'Monthly Fixed Customer Charge, $/month', 
        default=0.0,
        help_text='This charge is assessed every month, irrespective of usage.'
    )

    # Energy rate, 1st block
    rate1 = models.FloatField(
        'Rate for first block of usage, $/kWh',
        default=0.0
    )

    # 1st Block size, kWh
    block1 = models.FloatField(
        '1st Block size in kWh, leave blank to apply to all kWh',
        blank=True,
        null=True,
        help_text='Leave this entry blank if there are no usage blocks and the first rate applies to all kWh.'
    )

    # Energy rate, 2nd block
    rate2 = models.FloatField(
        'Rate for second block of usage, if present, $/kWh',
        blank=True,
        null=True,
        help_text='Only used if there is a second usage block.'
    )

    # Demand Charge
    demand_charge = models.FloatField(
        'Demand Charge for maximum 15 minute power, $/kW/mo',
        default=0.0,
        help_text='Generally not used except for Large Commercial rate structures.'
    )

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['sort_order', 'title']


class FuelRate(models.Model):
    """Defines a fuel rate.
    """
    # Name of the Rate Schedule
    title = models.CharField(max_length=80, unique=True)

    # Determines the order that the Rate Schedule will be presented in the UI
    sort_order = models.IntegerField(default=999)

    # Monthly fixed customer charge.
    customer_charge = models.FloatField(
        'Monthly Fixed Customer Charge, $/month', 
        default=0.0,
        help_text='This charge is assessed every month, irrespective of usage.'
    )

    # Fuel price expressed in $/MMBtu
    rate = models.FloatField(
        'Fuel Price expressed in $/MMBtu',
        default=0.0
    )

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['sort_order', 'title']


class Building(models.Model):
    '''
    A building that contains sensors.
    '''

    # name of the building displayed to users
    title = models.CharField(max_length=80, unique=True)

    # Latitude of building
    latitude = models.FloatField(default=61.13)

    # Longitude of building
    longitude = models.FloatField(default=-150.63)

    # Fields related to the Occupied Schedule of the Facility

    # The timezone, from the Olson timezone database, where the facility
    # is located.
    timezone = models.CharField("Time Zone of Facility, from tz database", 
        max_length=50, default='US/Alaska')

    # Occupied schedule for building.  No entry means continually occupied.
    schedule = models.TextField("Occupied Schedule of Facility (e.g. M-F: 8a-5p)", blank=True)

    # Current mode that building is in
    current_mode = models.ForeignKey(BuildingMode, models.SET_NULL, verbose_name='Current Operating Mode', blank=True, null=True)

    # Descriptive Text that shows at the bottom of the Current Values and Dashboard reports.
    report_footer = models.TextField(verbose_name='Additional Building Documentation', help_text='Use <a href="http://markdowntutorial.com/"> markdown syntax </a> to add links, pictures, etc.  Note that you <b>must</b> include the url prefix (e.g. <i>http://</i>) in your links.', blank=True, default='')

    # Timeline annotations
    timeline_annotations = models.TextField("Annotations for events in the building's timeline (e.g. Boiler Replaced: 1/1/2017)", help_text="One annotation per line. Use a colon between the annotation and the date/time.", blank=True)

    # Private Building Notes
    notes_private = models.TextField("Notes only seen by Sys Admins", help_text="Any text is valid and will only be seen by System Administrators.", blank=True)
 
    # Floor area of building
    floor_area = models.FloatField('Floor area of Building in square feet', null=True, blank=True)

    # Building Type
    SINGLE_RES = 'S-RES'
    MULTI_RES = 'M-RES'
    OFFICE = 'OFFIC'
    SCHOOL = 'SCH'
    RETAIL = 'RET'
    RESTAURANT = 'RES'
    WAREHOUSE = 'WARE'
    INDUSTRIAL = 'INDUS'
    OTHER = 'OTHER'

    BUILDING_TYPES = [
        (SINGLE_RES, 'Single-Family Residential'),
        (MULTI_RES, 'Multi-Family Residential'),
        (OFFICE, 'Office'),
        (SCHOOL, 'School'),
        (RETAIL, 'Retail'),
        (RESTAURANT, 'Restaurant'),
        (WAREHOUSE, 'Warehouse'),
        (INDUSTRIAL, 'Industrial'),
        (OTHER, 'Other')
    ]
    building_type = models.CharField(
        'Building Type',
        max_length=5,
        choices=BUILDING_TYPES,
        null=True,
        blank=True
    )

    # Electric Rate for Building
    electric_rate = models.ForeignKey(
        ElectricRate, 
        on_delete=models.SET_NULL, 
        verbose_name='Electric Rate Schedule for Building', 
        blank=True, null=True
    )

    # Fuel Rate for Building
    fuel_rate = models.ForeignKey(
        FuelRate, 
        on_delete=models.SET_NULL, 
        verbose_name='Primary Fuel Price for Building', 
        blank=True, null=True
    )

    # Building outdoor temperature sensor
    outdoor_temp = models.CharField(
        'Outdoor Temperature Sensor ID',
        max_length=80,
        blank=True
    )

    # Building Electric Power Sensors
    electric_ids = models.TextField(
        'Building Electric Power Sensor IDs, one per line',
        blank=True,
        help_text='Sensors will be added together to determine total electric use.'
    )

    # Building Fuel Use Sensors
    fuel_ids = models.TextField(
        'Building Fuel Use Sensor IDs, one per line',
        blank=True,
        help_text='Sensors will be added together to determine total fuel use.'
    )

    # Building Indoor Temperature Sensors
    indoor_temps = models.TextField(
        'Indoor Temperature Sensor IDs, one per line',
        blank=True
    )

    # Building Indoor Light Sensors
    indoor_lights = models.TextField(
        'Indoor Light Sensor IDs, one per line',
        blank=True
    )

    # CO2 Sensors
    co2_sensors = models.TextField(
        'CO2 Sensor IDs, one per line',
        blank=True
    )

    # Additional Descriptive Properties to include in the key_properties function.
    # These are given higer priority over the other fields so can be used to override 
    # other field values.
    other_properties = models.TextField("Additional Properties to include when exporting data. YAML form, e.g. age: 23", help_text="One property per line.  Name of Property, a colon, a space, and then the property value.", blank=True)

    # the sensors and calculated values associated with this building
    sensors = models.ManyToManyField(Sensor, through='BldgToSensor', blank=True)

    def __str__(self):
        return self.title

    def key_properties(self):
        """Returns a dictionary of important properties associated with this building.  Not all properties are 
        included.  One use is to include when exporting data.
        """
        # adding a 'building' qualifier to title because these props are often combined
        # with sensor properties that also have a title.
        props = {'building_title': self.title,
                 'latitude': self.latitude,
                 'longitude': self.longitude}
        try:
            props.update( yaml.load(self.other_properties, Loader=yaml.FullLoader) )
        except:
            # ignore errors
            pass
        
        return props

    def current_status(self, ts = time.time()):
        """Returns the occupied/unoccupied status of a building at a given time
        """
        if self.schedule:
            if self.timezone:
                scheduleObj = bmsapp.schedule.Schedule(self.schedule, self.timezone)
            else:
                scheduleObj = bmsapp.schedule.Schedule(self.schedule, 'US/Alaska')
            if scheduleObj.is_occupied(ts):
                return 'Occupied'
            else:
                return 'Unoccupied'
        else:
            return 'Occupied'

    class Meta:
        ordering = ['title']


class BuildingGroup(models.Model):
    """Defines a group of buildings that the user can select to filter the 
    buildings shown in the user interface.
    """
    
    # Name of the building group
    title = models.CharField(max_length=80, unique=True)
    
    # Determines the order that the building group will be presented in the UI
    sort_order = models.IntegerField(default=999)
    
    # The buildings that are present in this group
    buildings = models.ManyToManyField(Building)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['sort_order', 'title']
        

class BldgToSensor(models.Model):
    '''
    Links buildings to sensors and supplies additional information about what Sensor Group the sensor is 
    in and what order the sensor should be listed within the group.  The Bldg-to-Sensor link is set up as 
    Many-to-Many beacause weather station sensors or calculated values can be used by multiple different 
    buildings.
    '''

    # The building and sensor that are linked
    building = models.ForeignKey(Building, models.CASCADE)
    sensor = models.ForeignKey(Sensor, models.CASCADE)

    # For this building, the sensor group that the sensor should be classified in.
    # The default value is for the "Miscellaneous" Sensor Group.
    sensor_group = models.ForeignKey(SensorGroup, models.SET_DEFAULT, default=8)

    # Within the sensor group, this field determines the sort order of this sensor.
    sort_order = models.IntegerField(default=999)

    def __str__(self):
        return self.building.title + ": " + self.sensor.title

    class Meta:
        ordering = ('building__title', 'sensor_group__sort_order', 'sensor_group__title', 'sort_order', 'sensor__title')


class DashboardItem(models.Model):
    """An item on the Dashboard display for a building.
    """

    # The building this Dashboard item is for.
    building = models.ForeignKey(Building, models.CASCADE)

    # The Widget type to be used for display of this sensor on the Dashboard.
    GRAPH = 'graph'
    GAUGE = 'gauge'
    LED = 'LED'
    LABEL = 'label'
    NOT_CURRENT = 'stale'      # data is not current. Don't include as a User choice.
    DISPLAY_WIDGET_CHOICES = (
        (GRAPH, 'Graph'),
        (GAUGE, 'Gauge'),
        (LED, 'Red/Green LED'),
        (LABEL, 'Label'),
    )
    widget_type = models.CharField(max_length=15,
                                   choices=DISPLAY_WIDGET_CHOICES,
                                   default=GRAPH)

    # The row number on the Dashboard that this item will appear in.  Numbering can start
    # at any value and skip values; only the order matters.
    row_number = models.IntegerField(default=1)

    # The column number on the Dashboard that this item will appear in.  Numbering can
    # start at any value and can skip value; only the order matters.
    column_number = models.IntegerField(default=1)

    # The sensor, if any, used in this Dashboard item. This is actually a 
    # Building-to-Sensor object that contains a reference to a Sensor.
    sensor = models.ForeignKey(BldgToSensor, models.CASCADE, null=True, blank=True)

    # Title, mostly used for Label widgets, but also overrides default title on
    # other widgets
    title = models.CharField("Widget Title (can be blank)", max_length=50, null=True, blank=True)

    # The range of normal values
    minimum_normal_value = models.FloatField(default=0.0)
    maximum_normal_value = models.FloatField(default=100.0)

    # The total range of values shown on the Widget.  If blank,
    # default axis values will be calculated.
    minimum_axis_value = models.FloatField(null=True, blank=True)
    maximum_axis_value = models.FloatField(null=True, blank=True)

    def get_axis_range(self):
        """Returns the total range of values to show on the widget, using
        default values if none are provided by the user above.  A tuple of
        (min_axis_value, max_axis_value) is returned.
        """
        # Calculate the amount to extend the range beyond min and max normal
        # if no axis values are provided.  Base this on the range of normal
        # values.
        axis_extension = 0.60 * (self.maximum_normal_value - self.minimum_normal_value)
        min_val = self.minimum_axis_value if self.minimum_axis_value is not None else self.minimum_normal_value - axis_extension
        max_val = self.maximum_axis_value if self.maximum_axis_value is not None else self.maximum_normal_value + axis_extension
        return (min_val, max_val)

    def __str__(self):
        return self.widget_type + ": " + (self.sensor.sensor.title if self.sensor else self.title)

    class Meta:
        ordering = ('row_number', 'column_number', 'sensor__sort_order')


class MultiBuildingChart(models.Model):
    '''
    One particular chart that utilizes data from a group of buildings
    '''

    # descriptive title of the Chart
    title = models.CharField(max_length=60, unique=True)

    MULTI_CHART_CHOICES = (
        ('currentvalues_multi.CurrentValuesMulti', 'Current Sensor Values'),
        ('normalizedbyddbyft2.NormalizedByDDbyFt2', 'Energy / Degree-Day / ft2'),
        ('normalizedbyft2.NormalizedByFt2', 'Energy / ft2'),
    )

    # the type of chart
    chart_class = models.CharField("Type of Chart", 
                                    max_length=60,
                                    null=True,
                                    choices=MULTI_CHART_CHOICES)

    # the general parameters for this chart, if any.  These are parameters that are
    # *not* associated with a particular building.  The parameters are
    # entered in YAML format.
    parameters = models.TextField("General Chart Parameters in YAML Form", blank=True)

    # determines order of Chart displayed in Admin interface
    sort_order = models.IntegerField(default=999)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['sort_order']


class ChartBuildingInfo(models.Model):
    '''
    Information about a building that is used in an MultiBuildingChart.
    '''
    
    # the associated chart
    chart = models.ForeignKey(MultiBuildingChart, models.CASCADE)

    # the building participating in the Chart
    building = models.ForeignKey(Building, models.CASCADE)

    # the parameters for this chart associated with this building, if any.
    # The parameters are entered in YAML format.
    parameters = models.TextField("Chart Parameters in YAML Form", blank=True)

    # determines the order that this building appears in the chart
    sort_order = models.IntegerField(default=999)

    def __str__(self):
        return self.chart.title + ": " + self.building.title

    class Meta:
        ordering = ['sort_order']


class AlertRecipient(models.Model):
    '''A person or entity that is sent a notification when an Alert condition
    occurs.
    '''

    # If False, no alerts will be sent to this person
    active = models.BooleanField(default=True)

    # Name of recipient 
    name = models.CharField(max_length=50)

    # Email notification fields
    notify_email = models.BooleanField("Send Email?", default=True)
    email_address = models.EmailField(max_length=100, blank=True)

    # Cell Phone Text Message notification fields
    notify_cell = models.BooleanField("Send Text Message?", default=True)
    phone_regex = RegexValidator(regex=r'^\d{10}$', message="Phone number must be entered as a 10 digit number, including area code, no spaces, dashes or parens.")
    cell_number = models.CharField("10 digit Cell number", max_length=10, validators=[phone_regex], blank=True)
    cell_sms_gateway = models.CharField('Cell Phone Carrier', max_length=60, choices=sms_gateways.GATEWAYS, blank=True)

    # Pushover mobile app notification fields
    notify_pushover = models.BooleanField("Send Pushover Notification?", default=True)
    pushover_regex = RegexValidator(regex=r'^\w{30}$', message="Pushover ID should be exactly 30 characters long.")
    pushover_id = models.CharField('Pushover ID', validators=[pushover_regex], max_length=30, blank=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']

    def notify(self, subject, message, pushover_priority):
        '''If this recipient is active, sends a message to the recipient via each
         of the enabled communication means.  'subject' is the subject line of the
         message, and 'message' is the message.  For the Pushover notification
         service, 'pushover_priority' gives the priority string for the message
         (e.g. '0', '1', etc.)
         Retuns the number of successful messages sent.
        '''
        if not self.active:
            return 0

        msgs_sent = 0     # tracks successful messages sent.

        email_addrs = []
        if self.notify_email:
            email_addrs.append(self.email_address)
        if self.notify_cell:
            email_addrs.append('%s@%s' % (self.cell_number, self.cell_sms_gateway))

        if email_addrs:
            # The FROM email address
            from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', '')
            if from_email:
                try:
                    if send_mail(subject, message, from_email, email_addrs):
                        msgs_sent += len(email_addrs)
                except:
                    _logger.exception('Error sending mail to alert recipients.')
            else:
                _logger.exception('No From Email address configured in Settings file.')

        if self.notify_pushover:
            # Get the Pushover API key out of the settings file, setting it to None
            # if it is not present in the file.
            pushover_api_key = getattr(settings, 'BMSAPP_PUSHOVER_APP_TOKEN', None)
            if pushover_api_key:
                url = 'https://api.pushover.net/1/messages.json'
                payload = {'token': pushover_api_key,
                    'user': self.pushover_id,
                    'priority': pushover_priority,
                    'title': subject,
                    'message': message}
                if pushover_priority=='2':
                    # emergency priority requires a retry and expire parameter
                    payload['retry'] = 300
                    payload['expire'] = 7200
                resp = json.loads(requests.post(url, data=payload).text)
                if resp['status'] != 0:
                    msgs_sent += 1
                else:
                    _logger.exception(', '.join(resp['errors']))

            else:
                _logger.exception('No Pushover API Token Key configured in Settings file.')

        return msgs_sent

class AlertRecipientGroup(models.Model):
    """Defines a group of Alert Recipients. These can be assigned to individual AlertConditions
    and all of the recipients will be notified.
    """
    
    # Name of the Alert Recipient group
    title = models.CharField(max_length=80, unique=True)
 
    # The Alert Recipients that are present in this group
    recipients = models.ManyToManyField(AlertRecipient)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['title']


class AlertCondition(models.Model):
    '''A sensor condition that should trigger an Alert to be sent to AlertRecipient's.
    '''

    # If False, this condition will not be evaluated
    active = models.BooleanField(default=True, help_text='Uncheck the box to Disable the alert.')

    # the sensor this condition applies to
    sensor = models.ForeignKey(Sensor, models.CASCADE)

    CONDITION_CHOICES = (
        ('>', 'greater than'),
        ('>=', 'greater than or equal to'),
        ('<', 'less than'),
        ('<=', 'less than or equal to'),
        ('==', 'equal to'),
        ('!=', 'not equal to'),
        ('inactive', 'inactive'),
    )
    # conditional type to evaluate for the sensor value
    condition = models.CharField('Notify when the Sensor value is', max_length=20, default='>', choices=CONDITION_CHOICES)

    # the value to test the current sensor value against
    test_value = models.FloatField(verbose_name='this value', blank=True, null=True)

    # the number of readings that have to qualify before alerting
    READ_COUNT_CHOICES = (
        (1, '1 time'),
        (2, '2 times'),
        (3, '3 times'),
        (4, '4 times'),
        (5, '5 times')
    )
    read_count = models.PositiveSmallIntegerField('Number of times Condition must occur before alerting',
                                                  default=1, choices=READ_COUNT_CHOICES)

    # fields to qualify the condition test according to building mode
    only_if_bldg = models.ForeignKey(Building, models.SET_NULL, verbose_name='But only if building', blank=True, null=True)
    only_if_bldg_mode = models.ForeignKey(BuildingMode, models.SET_NULL, verbose_name='is in this mode', blank=True, null=True)
    only_if_bldg_status = models.CharField(verbose_name='and this status', max_length=15, blank=True, null=True, choices=(('Occupied','Occupied'),('Unoccupied','Unoccupied')))

    # alert message.  If left blank a message will be created from other field values.
    alert_message = models.TextField(max_length=400, blank=True,
        help_text='If left blank, a message will be created automatically.')

    # priority of the alert.  These numbers correspond to priority levels in Pushover.
    PRIORITY_LOW = '-1'
    PRIORITY_NORMAL = '0'
    PRIORITY_HIGH = '1'
    PRIORITY_EMERGENCY = '2'
    ALERT_PRIORITY_CHOICES = (
        (PRIORITY_LOW, 'Low'), 
        (PRIORITY_NORMAL, 'Normal'),
        (PRIORITY_HIGH, 'High'),
        (PRIORITY_EMERGENCY, 'Emergency')
    )
    priority = models.CharField('Priority of this Alert Situation', max_length=5, 
        choices=ALERT_PRIORITY_CHOICES,
        default=PRIORITY_NORMAL)

    # determines delay before notifying again about this condition.  Expressed in hours.
    wait_before_next = models.FloatField('Hours to Wait before Notifying Again', default=4.0)

    # the recipients who should receive this alert
    recipients = models.ManyToManyField(AlertRecipient, verbose_name='Who should be notified?', blank=True)

    # when the last notification of this alert condition was sent out, Unix timestamp.
    # This is filled out when alert conditions are evaluated and is not accessible in the Admin
    # interface.
    last_notified = models.FloatField(default=0.0)

    # the most recent result message for the alert.
    # This is filled out when alert conditions are evaluated and is not accessible in the Admin
    # interface.
    last_status = models.CharField(null=True, blank=True, default=None, max_length=255)

    def __str__(self):
        return '%s %s %s, %s in %s mode' % \
            (self.sensor.title, self.condition, self.test_value, self.only_if_bldg, self.only_if_bldg_mode)

    def handle(self, reading_db, logger, testing = False):
        '''This method handles an alert condition, notifying recipients if needed.
        If 'testing' is set to True, a message will always be sent. The number of alerts (0 or 1)
        is returned.
        '''
        alert_count = 0
        try:
            if testing:
                subject_msg = (f"Test Alert: {self.sensor.title} Sensor","This is just a test.")
            elif time.time() < (self.last_notified + self.wait_before_next * 3600.0):
                # if the wait time has not been satisfied, don't notify
                subject_msg =  None
            else:
                subject_msg = self.check_condition(reading_db)
            if subject_msg:
                alert_count = 1
                subject, msg = subject_msg
                msg_count = 0  # tracks # of successful messages sent
                for recip in self.recipients.all():
                    try:
                        msg_count += recip.notify(subject, msg, self.priority)
                    except:
                        logger.exception('Error notifying recipient %s of an alert.' % recip)
                if msg_count and (not testing):
                    # at least one message was sent so update the field tracking the timestamp
                    # of the last notification for this condition.
                    self.last_notified = time.time()
                    self.save()
                    # store a log of the alert
                    reading_db.log_alert(self.sensor.sensor_id,msg)

        except:
            logger.exception('Error processing alert %s')

        return alert_count

    def check_condition(self, reading_db, override_value = None):
        '''This method checks to see if the alert condition is in effect, and if so,
        returns a (subject, message) tuple describing the alert.  If the condition is 
        not in effect, None is returned.  'reading_db' is a sensor reading database, an 
        instance ofbmsapp.readingdb.bmsdata.BMSdata.  If an 'override_value' is
        specified, that value will be tested instead of the last values in the reading
        database. If the alert condition is not active, None is returned.
        '''

        if not self.active:
            has_alert = False   # condition not active
        else:
            # Make a description of the sensor that includes the building(s) it is
            # associated with.
            bldgs = [btos.building.title for btos in BldgToSensor.objects.filter(sensor__pk=self.sensor.pk)]
            bldgs_str = ', '.join(bldgs)
            sensor_desc = '%s sensor in %s' % (self.sensor.title, bldgs_str)

            # get the most current reading for the sensor (last_read), and
            # also fill out a list of all the recent readings that need to
            # be evaluated to determine if the alert condition is true (last_reads).
            if not override_value is None:
                last_read = {'ts': int(time.time()), 'val': float(override_value)}
                last_reads = [last_read]
            elif self.read_count==1:
                last_read = self.sensor.last_read(reading_db)  # will be None if no readings
                last_reads = [last_read] if last_read else []
            else:
                # last_read() method returns a list when read_count is > 1.
                last_reads = self.sensor.last_read(reading_db, self.read_count)
                last_read = last_reads[0] if len(last_reads) else None

            # if the condition test is for an inactive sensor, do that test now.
            # Do not consider the building mode test for this test.
            if self.condition=='inactive':
                if (not reading_db is None) and self.sensor.is_active(reading_db):
                    # Sensor is active, no alert
                    has_alert = False
                else:
                    # Sensor is inactive
                    has_alert = True

                    if last_read:
                        msg = 'The last reading from the %s was %.1f hours ago.' % \
                            ( sensor_desc, (time.time() - last_read['ts'])/3600.0 )
                    else:
                        msg = 'The %s has never posted a reading.' % sensor_desc

                    # Check for user-entered message, & use it ahead of standard message.
                    if self.alert_message.strip():
                        user_msg = self.alert_message.strip()
                        if user_msg[-1] != '.':
                            user_msg += '.'
                        msg = '%s %s' % (user_msg, msg)

                    subject = '%s Inactive' % sensor_desc

            elif len(last_reads) < self.read_count:
                # If there are not enough readings for this sensor, return as the
                # alert condition is not satisfied.
                has_alert = False

            elif (self.only_if_bldg is not None) and (self.only_if_bldg_mode is not None) and (self.only_if_bldg.current_mode != self.only_if_bldg_mode):
                # Failed building mode test
                has_alert = False

            elif (self.only_if_bldg is not None) and (self.only_if_bldg_status is not None) and (self.only_if_bldg.current_status(last_reads[0]['ts']) != self.only_if_bldg_status):
                # Failed building status test
                has_alert = False

            elif not all([eval( '%s %s %s' % (read['val'], self.condition, self.test_value) ) for read in last_reads]):
                # Loop through the requested number of last readings, testing whether
                # the alert conditions are satisfied for all the readings.
                # Alert condition must be true for each of the requested readings
                has_alert = False

            else:
                # All of the alert conditions were satisfied,
                # return a subject and message.
                has_alert = True

                # Get a formatting function for sensor values
                formatter = self.sensor.format_func()
                condition_text = choice_text(self.condition, AlertCondition.CONDITION_CHOICES)
                subject = '%s is %s %s' % (sensor_desc, condition_text, formatter(self.test_value))
                if self.alert_message.strip():
                    msg = self.alert_message.strip()
                    if msg[-1] != '.':
                        msg += '.'
                    msg = '%s The current sensor reading is %s %s.' % \
                        (msg, formatter(last_read['val']), self.sensor.unit.label)
                else:
                    msg = 'The %s has a current reading of %s %s, which is %s %s %s.' % \
                        (
                        sensor_desc,
                        formatter(last_read['val']),
                        self.sensor.unit.label,
                        condition_text,
                        formatter(self.test_value),
                        self.sensor.unit.label
                        )
                    
        if has_alert:
            current_status = subject
            return_value = '%s Priority Alert: ' % choice_text(self.priority, AlertCondition.ALERT_PRIORITY_CHOICES) + subject, msg
        else:
            current_status = None
            return_value = None

        if self.last_status != current_status:
            self.last_status = current_status
            self.save()

        return return_value

    def wait_satisfied(self):
        '''Returns True if there has been enough wait between the last notification
        for this condition and now.
        '''
        return (time.time() >= self.last_notified + self.wait_before_next * 3600.0)


class PeriodicScript(models.Model):
    """Describes a script that should be run on a periodic basis,
    often for the purposes of collecting sensor readings to store in the
    reading database.
    """

    # Name of the script file
    script_file_name = models.CharField('File name of script', max_length=50, blank=False)

    # Optional Description
    description = models.CharField('Optional Description', max_length=80, blank=True)

    # How often the script should be run, in units of seconds.
    # Use defined choices; choices must be a multiple of 5 minutes, as that is
    # how frequently the main cron procedure runs.
    PERIOD_CHOICES = (
        (0, 'Disabled'),
        (300, '5 min'),
        (600, '10 min'),
        (900, '15 min'),
        (1800, '30 min'),
        (3600, '1 hr'),
        (7200, '2 hr'),
        (14400, '4 hr'),
        (21600, '6 hr'),
        (43200, '12 hr'),
        (86400, '24 hr')
    )
    period = models.IntegerField('How often should script run', default=3600, choices=PERIOD_CHOICES)

    # Parameters for the script, if any, given in YAML form.
    script_parameters = models.TextField("Script Parameters in YAML form", blank=True)

    # Results of the script saved and passed to the next invocation of the script.
    script_results = models.TextField('Script results in YAML form', blank=True)

    # Results of the Script that are *not* displayed in the Admin interface.  Useful
    # for storing authorization tokens or other credentials.
    hidden_script_results = models.TextField('Hidden Script results in YAML form', blank=True)

    def __str__(self):
        return '%s -- %s' % (self.script_file_name, self.script_parameters.replace('\n', ', '))

class CustomReport(models.Model):
    """Defines a custom report with text and widgets defined by the user.
    """
    
    # Name of the group that the report is listed under
    group = models.CharField(max_length=80)

    # Name of the report
    title = models.CharField(max_length=80)
    
    # Determines the order within the group that the report will be presented in the UI
    sort_order = models.IntegerField(default=999)
    
    # Markdown text that defines what will appear in the report
    markdown_text = models.TextField(verbose_name='Report Content (in markdown):', help_text='Use <a href="http://markdowntutorial.com/">markdown syntax</a> to add links, pictures, etc.  Note that you <b>must</b> include the url prefix (e.g. <i>http://</i>) in any external links.', blank=True)    

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['group','sort_order', 'title']
        

class Organization(models.Model):
    """Defines an Organization that the user can use to filter the 
    buildings and building groups shown in the user interface.
    """
    
    # Name of the Organization
    title = models.CharField(max_length=80, unique=True)
    
    # Determines the order that the Organization will be presented in the UI
    sort_order = models.IntegerField(default=999)
    
    # The buildings that are present in this Organization
    buildings = models.ManyToManyField(Building)
    
    # The building groups that are present in this Organization
    building_groups = models.ManyToManyField(BuildingGroup, blank=True)

    # Multi-Building Charts associated with this Organization
    multi_charts = models.ManyToManyField(MultiBuildingChart, blank=True)

    # Custom Reports associated with this Organization
    custom_reports = models.ManyToManyField(CustomReport, blank=True)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['sort_order', 'title']


def choice_text(val, choices):
    """Returns the display text associated with the choice value 'val'
    from a list of Django character field choices 'choices'.  The 'choices'
    list is a list of two-element tuples, the first item being the stored
    value and the second item being the displayed value.  Returns None if 
    val is not found inthe choice list.
    """
    for choice in choices:
        if choice[0]==val:
            return choice[1]
    return None
