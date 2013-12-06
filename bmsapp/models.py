from django.db import models

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
    sensor_id = models.CharField("Monnit Sensor ID, or Calculated Field ID", max_length=15, unique=True)

    # descriptive title for the sensor, shown to users
    title = models.CharField(max_length = 50)

    # the units for the sensor values
    unit =  models.ForeignKey(Unit)

    # if True, this field is a calculated field and is not directly created from a sensor.
    is_calculated = models.BooleanField("Calculated Field")

    # the name of the transform function to scale the value, if any, for a standard sensor field, or the 
    # calculation function (required) for a calculated field.  transform functions must be located in the 
    # "transforms.py" module in the "calcs" package and calculated field functions must be properly 
    # referenced in the "calc_readings.py" script in the "scripts" directory.
    tran_calc_function = models.CharField("Transform or Calculated Field Function Name", max_length=35, blank=True)

    # the function parameters, if any, for the transform or calculation function above.  parameters are 
    # entered as one comma-separated string in keyword style, such as 'id_flow="124356", heat_capacity=40.2'
    function_parameters = models.TextField("Function Parameters in Keyword form", blank=True)

    # Calculation order.  If this particular calculated field depends on the completion of other calculated fields
    # first, make sure the calculation_order for this field is higher than the fields it depends on.
    calculation_order = models.IntegerField(default=0)

    def __unicode__(self):
        return self.sensor_id + ": " + self.title

    class Meta:
        ordering = ['sensor_id']


class MultiBuildingChartType(models.Model):
    '''
    A type of chart that uses data from multiple buildings
    '''

    # descriptive title of the Chart Type
    title = models.CharField(max_length=50, unique=True)

    # the name of the Javascript class used to render the chart.  Also the
    # name of the Django template name used to create the HTML for the chart.
    class_name = models.CharField(max_length=30, unique=True)

    # determines order of Chart Type displayed in Admin interface
    sort_order = models.IntegerField(default=999)

    def __unicode__(self):
        return self.title

    class Meta:
        ordering = ['sort_order']


class Building(models.Model):
    '''
    A building that contains sensors.
    '''

    # name of the building displayed to users
    title = models.CharField(max_length=50, unique=True)

    # the sensors and calculated values associated with this building
    sensors = models.ManyToManyField(Sensor, through='BldgToSensor', blank=True, null=True)

    def __unicode__(self):
        return self.title

    class Meta:
        ordering = ['title']


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


class MultiBuildingChart(models.Model):
    '''
    One particular chart that utilizes data from a group of buildings
    '''

    # descriptive title of the Chart
    title = models.CharField(max_length=60, unique=True)

    # the type of chart
    chart_type = models.ForeignKey(MultiBuildingChartType)

    # the general parameters for this chart, if any.  These are parameters that are
    # *not* associated with a particular building.  The parameters are
    # entered as one comma-separated string in keyword style, 
    # such as 'id_flow="124356", heat_capacity=40.2'
    parameters = models.TextField("General Chart Parameters in Keyword Form", blank=True)

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
    # The parameters are entered as one comma-separated string in keyword style, 
    # such as 'id_flow="124356", heat_capacity=40.2'
    parameters = models.TextField("Chart Parameters in Keyword Form", blank=True)

    # determines the order that this building appears in the chart
    sort_order = models.IntegerField(default=999)

    def __unicode__(self):
        return self.chart.title + ": " + self.building.title

    class Meta:
        ordering = ['sort_order']

