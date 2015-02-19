from django.db import models
from django.core.validators import RegexValidator
import sms_gateways


# Models for the BMS App

class SensorGroup(models.Model):
    '''
    A functional group that the sensor belongs to, e.g. "Weather, Snowmelt System".
    '''

    # the diplay name of the Sensor Group.
    title = models.CharField(max_length=40, unique=True)

    # A number that determines the order that Sensor Groups will be presented to the user.
    sort_order = models.IntegerField(default=999)

    def __unicode__(self):
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

    def __unicode__(self):
        return '%s: %s' % (self.measure_type, self.label)

    class Meta:
        ordering = ['measure_type', 'label']


class Sensor(models.Model):
    '''
    One sensor or a calculated field
    '''

    # sensor ID, either from Monnit network or a user-entered ID for a calculated value
    sensor_id = models.CharField("Monnit Sensor ID, or Calculated Field ID", max_length=30, unique=True)

    # descriptive title for the sensor, shown to users
    title = models.CharField(max_length = 50)

    # the units for the sensor values
    unit =  models.ForeignKey(Unit)

    # if True, this field is a calculated field and is not directly created from a sensor.
    is_calculated = models.BooleanField("Calculated Field", default=False)

    # the name of the transform function to scale the value, if any, for a standard sensor field, or the 
    # calculation function (required) for a calculated field.  transform functions must be located in the 
    # "transforms.py" module in the "calcs" package and calculated field functions must be properly 
    # referenced in the "calc_readings.py" script in the "scripts" directory.
    tran_calc_function = models.CharField("Transform or Calculated Field Function Name", max_length=35, blank=True)

    # the function parameters, if any, for the transform or calculation function above.  parameters are 
    # entered in YAML format.
    function_parameters = models.TextField("Function Parameters in YAML form", blank=True)

    # Calculation order.  If this particular calculated field depends on the completion of other calculated fields
    # first, make sure the calculation_order for this field is higher than the fields it depends on.
    calculation_order = models.IntegerField(default=0)

    # the name of the formatting function for the value, if any.
    # Formatting functions must be located in the "formatters.py" module.
    formatting_function = models.CharField("Formatting Function Name", max_length=50, blank=True)

    def __unicode__(self):
        return self.sensor_id + ": " + self.title

    class Meta:
        ordering = ['sensor_id']


class BuildingMode(models.Model):
    '''A state or mode that the building could be in, such as Winter, Summer, Vacant.
    '''

    # name of the mode
    name = models.CharField("Mode Name", max_length=50)

    def __unicode__(self):
        return self.name


class Building(models.Model):
    '''
    A building that contains sensors.
    '''

    # name of the building displayed to users
    title = models.CharField(max_length=50, unique=True)

    # Current mode that building is in
    current_mode = models.ForeignKey(BuildingMode, verbose_name='Current Operating Mode', blank=True, null=True)

    # Latitude of building
    latitude = models.FloatField(default=62.0)

    # Longitude of building
    longitude = models.FloatField(default=-161.0)

    # Fields related to the Occupied Schedule of the Facility

    # The timezone, from the Olson timezone database, where the facility
    # is located.
    timezone = models.CharField("Time Zone of Facility, from tz database", 
        max_length=50, default='US/Alaska')

    # Occupied schedule for building.  No entry means continually occupied.
    schedule = models.TextField("Occupied Schedule of Facility (e.g. M-F: 8a-5p)", blank=True)

    # the sensors and calculated values associated with this building
    sensors = models.ManyToManyField(Sensor, through='BldgToSensor', blank=True, null=True)

    def __unicode__(self):
        return self.title

    class Meta:
        ordering = ['title']


class BuildingGroup(models.Model):
    """Defines a group of buildings that the user can select to filter the 
    buildings shown in the user interface.
    """
    
    # Name of the building group
    title = models.CharField(max_length=50, unique=True)
    
    # Determines the order that the building group will be presented in the UI
    sort_order = models.IntegerField(default=999)
    
    # The buildings that are present in this group
    buildings = models.ManyToManyField(Building)

    def __unicode__(self):
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
    building = models.ForeignKey(Building)
    sensor = models.ForeignKey(Sensor)

    # For this building, the sensor group that the sensor should be classified in.
    sensor_group = models.ForeignKey(SensorGroup)

    # Within the sensor group, this field determines the sort order of this sensor.
    sort_order = models.IntegerField(default=999)

    def __unicode__(self):
        return self.building.title + ": " + self.sensor.title

    class Meta:
        ordering = ('building__title', 'sensor_group__sort_order', 'sort_order')


class DashboardItem(models.Model):
    """An item on the Dashboard display for a building.
    """

    # The building this Dashboard item is for.
    building = models.ForeignKey(Building)

    # The Widget type to be used for display of this sensor on the Dashboard.
    GAUGE = 'gauge'
    LED = 'LED'
    LABEL = 'label'
    NOT_CURRENT = 'stale'      # data is not current. Don't include as a User choice.
    DISPLAY_WIDGET_CHOICES = (
        (GAUGE, 'Gauge'),
        (LED, 'Red/Green LED'),
        (LABEL, 'Label'),
    )
    widget_type = models.CharField(max_length=15,
                                   choices=DISPLAY_WIDGET_CHOICES,
                                   default=GAUGE)

    # The row number on the Dashboard that this item will appear in.  Numbering can start
    # at any value and skip values; only the order matters.
    row_number = models.IntegerField(default=1)

    # The column number on the Dashboard that this item will appear in.  Numbering can
    # start at any value and can skip value; only the order matters.
    column_number = models.IntegerField(default=1)

    # The sensor, if any, used in this Dashboard item
    sensor = models.ForeignKey(BldgToSensor, null=True, blank=True)

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

    def __unicode__(self):
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

    def __unicode__(self):
        return self.title

    class Meta:
        ordering = ['sort_order']


class ChartBuildingInfo(models.Model):
    '''
    Information about a building that is used in an MultiBuildingChart.
    '''
    
    # the associated chart
    chart = models.ForeignKey(MultiBuildingChart)

    # the building participating in the Chart
    building = models.ForeignKey(Building)

    # the parameters for this chart associated with this building, if any.
    # The parameters are entered in YAML format.
    parameters = models.TextField("Chart Parameters in YAML Form", blank=True)

    # determines the order that this building appears in the chart
    sort_order = models.IntegerField(default=999)

    def __unicode__(self):
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

    def __unicode__(self):
        return self.name


class AlertCondition(models.Model):
    '''A sensor condition that should trigger an Alert to be sent to AlertRecipient's.
    '''

    # If False, this condition will not be evaluated
    active = models.BooleanField(default=True, help_text='Uncheck the box to Disable the alert.')

    # the sensor this condition applies to
    sensor = models.ForeignKey(Sensor)

    CONDITION_CHOICES = (
        ('>', '>'),
        ('>=', '>='),
        ('<', '<'),
        ('<=', '<='),
        ('==', 'equal to'),
        ('!=', 'not equal to'),
        ('inactive', 'inactive'),
    )
    # conditional type to evaluate for the sensor value
    condition = models.CharField('Notify when the Sensor value is', max_length=20, choices=CONDITION_CHOICES)

    # the value to test the current sensor value against
    test_value = models.FloatField(verbose_name='this value', blank=True, null=True)

    # fields to qualify the condition test according to building mode
    only_if_bldg = models.ForeignKey(Building, verbose_name='But only if building', blank=True, null=True)
    only_if_bldg_mode = models.ForeignKey(BuildingMode, verbose_name='is in this mode', blank=True, null=True)

    # alert message.  If left blank a message will be created from other field values.
    alert_message = models.TextField(max_length=200, blank=True, 
        help_text='If left blank, a message will be created.  Use the string "{val}" in the message to show the current sensor value.')

    # priority of the alert.  These numbers correspond to priority levels in Pushover.
    PRIORITY_LOW = '-1'
    PRIORITY_NORMAL = '0'
    PRIORITY_HIGH = '1'
    ALERT_PRIORITY_CHOICES = ( 
        (PRIORITY_LOW, 'Low'), 
        (PRIORITY_NORMAL, 'Normal'),
        (PRIORITY_HIGH, 'High'),
    )
    priority = models.CharField('Priority of this Alert Situation', max_length=5, 
        choices=ALERT_PRIORITY_CHOICES,
        default=PRIORITY_NORMAL)

    # determines delay before notifying again about this condition.  Expressed in hours.
    wait_before_next = models.FloatField('Hours to Wait before Notifying Again', default=4.0)

    # the recipients who should receive this alert
    recipients = models.ManyToManyField(AlertRecipient, verbose_name='Who should be notified?')

    # when the last notification of this alert condition was sent out, Unix timestamp.
    # This is filled out when alert conditions are evaluated and is not accessible in the Admin
    # interface.
    last_notified = models.FloatField(blank=True, null=True)

    def __unicode__(self):
        return '%s %s %s' % (self.sensor.title, self.condition, self.test_value)
