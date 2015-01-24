import time
from django.template import Context, loader
import bmsapp.models, bmsapp.data_util
import bmsapp.formatters
import basechart


class CurrentValues(basechart.BaseChart):
    """Class that creates the Current Values report.
    """

    def result(self):

        # make a list with the major items being a sensor group and the 
        # minor items being a list of sensor info: 
        #   (sensor name, most recent value, units, how many minutes ago value occurred)
        cur_group = ''
        cur_group_sensor_list = []
        sensor_list = []
        cur_time = time.time()   # needed for calculating how long ago reading occurred
        for b_to_sen in self.building.bldgtosensor_set.all():
            if b_to_sen.sensor_group.title != cur_group:
                if cur_group:
                    sensor_list.append( (cur_group, cur_group_sensor_list) )
                cur_group = b_to_sen.sensor_group.title
                cur_group_sensor_list = []
            last_read = self.reading_db.last_read(b_to_sen.sensor.sensor_id)
            if b_to_sen.sensor.formatting_function:
                format_function = getattr(bmsapp.formatters,b_to_sen.sensor.formatting_function)
                cur_value = format_function(last_read['val']) if last_read else ''
            else:
                cur_value = bmsapp.data_util.formatCurVal(last_read['val']) if last_read else ''
            minutes_ago = '%.1f' % ((cur_time - last_read['ts'])/60.0) if last_read else ''
            cur_group_sensor_list.append( {'title': b_to_sen.sensor.title, 
                                           'cur_value': cur_value, 
                                           'unit': b_to_sen.sensor.unit.label,
                                           'minutes_ago': minutes_ago,
                                           'sensor_id': b_to_sen.sensor.id} )
        # add the last group
        if cur_group:
            sensor_list.append( (cur_group, cur_group_sensor_list) )

        # context for template
        context = Context( {} )
        
        # make this sensor list available to the template
        context['sensor_list'] = sensor_list

        # create a report title
        context['report_title'] = 'Current Values: %s' % self.building.title

        # template needs building ID.
        context['bldg_id'] = self.bldg_id

        # Get the ID of the first time series chart for this building
        context['ts_chart_id'] = basechart.TIME_SERIES_CHART_ID

        template = loader.get_template('bmsapp/CurrentValues.html')
        return {'html': template.render(context), 'objects': []}

