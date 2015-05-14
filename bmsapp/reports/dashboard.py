import time
import bmsapp.models
import bmsapp.data_util
import bmsapp.formatters
import basechart

class Dashboard(basechart.BaseChart):
    """Class for creating Dashboard report.
    """

    # see BaseChart for definition of these constants
    CTRLS = 'refresh'
    TIMED_REFRESH = 1

    def result(self):
        """Create the dashboard HTML and configuration object.
        """

        widgets = []
        cur_row = []
        cur_row_num = None
        for dash_item in self.building.dashboarditem_set.all():
            if dash_item.row_number != cur_row_num:
                if len(cur_row):
                    widgets.append(cur_row)
                cur_row = []
                cur_row_num = dash_item.row_number
    
            new_widget = {'type': dash_item.widget_type}
            # Determine title, either from user entry or from sensor's title
            new_widget['title'] = dash_item.title if len(dash_item.title) or (dash_item.sensor is None) else dash_item.sensor.sensor.title

            if dash_item.sensor is not None:
                last_read = dash_item.sensor.sensor.last_read(self.reading_db)
                format_function = dash_item.sensor.sensor.format_func()
                cur_value = last_read['val'] if last_read else None
                new_widget['value_label'] = format_function(last_read['val']) if last_read else ''
                age_secs = time.time() - last_read['ts'] if last_read else None    # how long ago reading occurred
                minAxis, maxAxis = dash_item.get_axis_range()
                new_widget.update( {'units': dash_item.sensor.sensor.unit.label,
                                    'value': cur_value,
                                    'minNormal': dash_item.minimum_normal_value,
                                    'maxNormal': dash_item.maximum_normal_value,
                                    'minAxis': min(minAxis, cur_value),
                                    'maxAxis': max(maxAxis, cur_value),
                                    'timeChartID': basechart.TIME_SERIES_CHART_ID,
                                    'sensorID': dash_item.sensor.sensor.id,
                                   } )
                # check to see if data is older than 2 hours or missing, and change widget type if so.
                if cur_value is None:
                    new_widget['type'] = bmsapp.models.DashboardItem.NOT_CURRENT
                    new_widget['age'] = 'Not Available'
                elif 7200 <= age_secs < 86400:
                    new_widget['type'] = bmsapp.models.DashboardItem.NOT_CURRENT
                    new_widget['age'] = '%.1f hours Old' % (age_secs/3600.0)
                elif age_secs >= 86400:
                    new_widget['type'] = bmsapp.models.DashboardItem.NOT_CURRENT
                    new_widget['age'] = '%.1f days Old' % (age_secs/86400.0)

            cur_row.append(new_widget)

        # append the last row if anything is present in that row
        if len(cur_row):
            widgets.append(cur_row)

        dash_config = {'widgets': widgets, 'renderTo': 'dashboard'}

        html = '''<h2 id="report_title">%s Dashboard</h2>
        <div id="dashboard" style="background: #FFFFFF"></div>''' % self.building.title

        return {'html': html, 'objects': [('dashboard', dash_config)]}


