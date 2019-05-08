import yaml
import time
from django.template import loader
import bmsapp.models, bmsapp.data_util, bmsapp.view_util
import bmsapp.formatters
from . import basechart


class CurrentValuesMulti(basechart.BaseChart):
    """Class that creates the Current Values Multi-Building report.
    """
    
    # see BaseChart for definition of these constants
    CTRLS = 'refresh, get_embed_link'
    TIMED_REFRESH = 1
    
    def result(self):
        # get the current time for calculating how long ago reading occurred
        cur_time = time.time()

        org_id = int(self.request_params.get('select_org', 0))
        # get the buildings in the current building group
        building_group_id = int(self.request_params['select_group'])
        buildings = bmsapp.view_util.buildings_for_group(building_group_id)

        # create a blank list to store the sensor values for the report
        sensor_list = []

        # create a blank dictionary to store value ranges for each unit
        # the dictionary is keyed on unit_label, values are dictionaries with 'min' and 'max' keys
        value_ranges = {}

        # loop through the selected buildings
        for bldg_info in self.chart_info.chartbuildinginfo_set.filter(building__in=buildings):

            # get the parameters associated with this building
            sensors = yaml.load(bldg_info.parameters, Loader=yaml.FullLoader)

            # make a list with items being a list of sensor info:
            #   (sensor name, most recent value, units, how many minutes ago value occurred)
            building_sensor_list = []

            for b_to_sen in bldg_info.building.bldgtosensor_set.filter(sensor__sensor_id__in=sensors):
                last_read = b_to_sen.sensor.last_read(self.reading_db)
                format_function = b_to_sen.sensor.format_func()
                cur_value = format_function(last_read['val']) if last_read else ''
                minutes_ago = '%.1f' % ((cur_time - last_read['ts'])/60.0) if last_read else ''

                # update the values in the value_ranges dictionary
                if b_to_sen.sensor.unit.label in value_ranges:
                    unit_range = value_ranges[b_to_sen.sensor.unit.label]
                    unit_range['min'] = min(unit_range['min'], last_read['val'])
                    unit_range['max'] = max(unit_range['max'], last_read['val'])
                else:
                    unit_range = {'min': last_read['val'], 'max': last_read['val']}
                value_ranges[b_to_sen.sensor.unit.label] = unit_range

                building_sensor_list.append({ 'group': b_to_sen.sensor_group.title,
                                              'title': b_to_sen.sensor.title,
                                              'cur_value': cur_value,
                                              'last_read': last_read['val'],
                                              'unit': b_to_sen.sensor.unit.label,
                                              'minutes_ago': minutes_ago,
                                              'sensor_id': b_to_sen.sensor.id,
                                              'notes': '%s<br>ID: %s' % (b_to_sen.sensor.notes, b_to_sen.sensor.sensor_id),
                                              'href': '?select_org={}&select_group={}&select_bldg={}&select_chart={}&select_sensor_multi={}'.format(org_id, self.request_params['select_group'], bldg_info.building.pk, basechart.TIME_SERIES_CHART_ID, b_to_sen.sensor.id) ,
                                              'building_href': '?select_group={}&select_bldg={}'.format(self.request_params['select_group'], bldg_info.building.pk) ,
                                              'alerts': '; '.join([message for subject, message in b_to_sen.sensor.alerts(self.reading_db)])})

            sensor_list.append({'bldg_name': bldg_info.building.title,
                                'bldg_id': bldg_info.building.pk,
                                'group_sensor_list': building_sensor_list
                                })

        # add the percentage info for sensors
        for building_info in sensor_list:
            for sensor in building_info['group_sensor_list']:
                value_range = value_ranges[sensor['unit']]
                if value_range['max'] != value_range['min']:
                    last = sensor['last_read'] - value_range['min']
                    high = value_range['max'] - value_range['min']
                    sensor['pct'] = last / high
                    sensor['stars'] = '*' * (int((last / high) * 9) + 1)
                else:
                    sensor['pct'] = 0
                    sensor['stars'] = ''


        # context for template
        context = {}

        # create a report title
        context['report_title'] = self.chart_info.title

        # make this sensor list available to the template
        context['sensor_list'] = sensor_list

        # Get the ID of the first time series chart for a building
        context['ts_chart_id'] = basechart.TIME_SERIES_CHART_ID

        template = loader.get_template('bmsapp/CurrentValuesMulti.html')
        return {'html': template.render(context), 'objects': []}

