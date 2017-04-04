import time
import bmsapp.models
import bmsapp.data_util
import bmsapp.formatters
import basechart
import markdown
from datetime import datetime
import pytz


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

        maxTime = time.time() + (60 * 10) # 10 minutes from now to avoid the icon falling off the chart
        minTime = time.time() - (60 * 60 * 4) # 4 hours ago
        tz = pytz.timezone(self.timezone)

        for dash_item in self.building.dashboarditem_set.all():
            if dash_item.row_number != cur_row_num:
                if len(cur_row):
                    widgets.append(cur_row)
                cur_row = []
                cur_row_num = dash_item.row_number
    
            new_widget = {'type': dash_item.widget_type,
                          'timeChartID': basechart.TIME_SERIES_CHART_ID,
                          'title': dash_item.title if len(dash_item.title) or (dash_item.sensor is None) else dash_item.sensor.sensor.title
                          }

            if dash_item.sensor is not None:
                times = []
                values = []
                labels = []
                format_function = dash_item.sensor.sensor.format_func()
                minAxis, maxAxis = dash_item.get_axis_range()

                # Retrieve active alert settings
                alerts = []
                try:
                    for alert_condx in bmsapp.models.AlertCondition.objects.filter(sensor__pk=dash_item.sensor.sensor.pk):
                        if alert_condx.only_if_bldg is not None and alert_condx.only_if_bldg_mode is not None:
                            bldg_mode_test = (alert_condx.only_if_bldg.current_mode == alert_condx.only_if_bldg_mode)
                        else:
                            bldg_mode_test = True
                        if bldg_mode_test:
                            alerts.append({'condition': alert_condx.condition, 'value': alert_condx.test_value})
                except Exception as e:
                    pass

                db_recs = self.reading_db.rowsForOneID(dash_item.sensor.sensor.sensor_id, minTime, maxTime)

                if db_recs:
                    for rec in db_recs:
                        times.append(datetime.fromtimestamp(rec['ts'],tz).strftime('%Y-%m-%d %H:%M:%S'))
                        values.append(bmsapp.data_util.round4(rec['val']))
                        labels.append(datetime.fromtimestamp(rec['ts'],tz).strftime('%I:%M %p').lstrip('0') + '</br>' + format_function(rec['val']) + ' ' + dash_item.sensor.sensor.unit.label)
                    minAxis = min(minAxis, min(values))
                    maxAxis = max(maxAxis, max(values))
                    if dash_item.sensor.sensor.unit.label not in ['code','1=On 0=Off']:
                        value_label = format_function(values[-1]) + ' ' + dash_item.sensor.sensor.unit.label
                    else:
                        value_label = format_function(values[-1])
                    if dash_item.minimum_normal_value <= values[-1] <= dash_item.maximum_normal_value:
                        value_is_normal = True
                    else:
                        value_is_normal = False
                else:
                    # db_recs = None
                    value_is_normal = False
                    last_read = dash_item.sensor.sensor.last_read(self.reading_db)
                    cur_value = float(bmsapp.data_util.formatCurVal(last_read['val']).translate(None, ',')) if last_read else None
                    if cur_value is None:
                        value_label = 'No Data Available!'
                    else:
                        age_secs = time.time() - last_read['ts']    # how long ago reading occurred
                        if age_secs < 86400:
                            value_label = 'Last reading was %.1f hours ago' % (age_secs/3600.0)
                        elif age_secs >= 86400:
                            value_label = 'Last reading was %.1f days ago' % (age_secs/86400.0)

                new_widget.update( {
                    'sensorID': dash_item.sensor.sensor.id,
                    'value_label': value_label,
                    'value_is_normal': value_is_normal,
                    'times': times,
                    'values': values,
                    'labels': labels,
                    'minNormal': dash_item.minimum_normal_value,
                    'maxNormal': dash_item.maximum_normal_value,
                    'minAxis': minAxis,
                    'maxAxis': maxAxis,
                    'minTime': datetime.fromtimestamp(minTime,tz).strftime('%Y-%m-%d %H:%M:%S'),
                    'maxTime': datetime.fromtimestamp(maxTime,tz).strftime('%Y-%m-%d %H:%M:%S'),
                    'units': dash_item.sensor.sensor.unit.label,
                    'unitMeasureType': dash_item.sensor.sensor.unit.measure_type,
                    'href': '{}?select_group={}&select_bldg={}&select_chart={}&select_sensor={}'.format(self.request.build_absolute_uri('/reports/'), self.request_params['select_group'], self.bldg_id, basechart.TIME_SERIES_CHART_ID, dash_item.sensor.sensor.id) ,
                    'alerts': alerts
                    } )
    
            else:
                # dash_item.sensor = None
                pass

            cur_row.append(new_widget)

        # append the last row if anything is present in that row
        if len(cur_row):
            widgets.append(cur_row)

        dash_config = {'widgets': widgets, 'renderTo': 'dashboard'}
        
        footer = markdown.markdown(self.building.report_footer)

        if footer:
            footer_title = "Additional Building Documentation for %s:" % self.building.title
        else: 
            footer_title = ""
            
        html = '''<h2 id="report_title">%s Dashboard</h2>
        <div id="dashboard" style="background: #FFFFFF"></div>
        <div style="clear:both"></div>
        <h3>%s</h3>
        %s''' % (self.building.title, footer_title, footer)

        return {'html': html, 'objects': [('dashboard', dash_config)]}


