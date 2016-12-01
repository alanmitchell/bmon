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

        maxTime = time.time()
        minTime = maxTime - (60 * 60 * 4) # 4 hours
        tz = pytz.timezone(self.timezone)

        for dash_item in self.building.dashboarditem_set.all():
            if dash_item.row_number != cur_row_num:
                if len(cur_row):
                    widgets.append(cur_row)
                cur_row = []
                cur_row_num = dash_item.row_number
    
            new_widget = {'type': dash_item.widget_type,
                          'timeChartID': basechart.TIME_SERIES_CHART_ID,
                          'sensorID': dash_item.sensor.sensor.id
                          }

            # Determine title, either from user entry or from sensor's title
            new_widget['title'] = dash_item.title if len(dash_item.title) or (dash_item.sensor is None) else dash_item.sensor.sensor.title

            if dash_item.sensor is not None:
                times = []
                values = []
                labels = []
                format_function = dash_item.sensor.sensor.format_func()

                db_recs = self.reading_db.rowsForOneID(dash_item.sensor.sensor.sensor_id, minTime, maxTime)

                if db_recs:
                    for rec in db_recs:
                        times.append(datetime.fromtimestamp(rec['ts'],tz).strftime('%Y-%m-%d %H:%M:%S'))
                        values.append(bmsapp.data_util.round4(rec['val']))
                        labels.append(datetime.fromtimestamp(rec['ts'],tz).strftime('%I:%M %p').lstrip('0') + '</br>' + format_function(rec['val']) + ' ' + dash_item.sensor.sensor.unit.label)

                    new_widget['value_label'] = format_function(values[-1])
                    minAxis, maxAxis = dash_item.get_axis_range()
                    new_widget.update( {'units': dash_item.sensor.sensor.unit.label,
                                        'value': values[-1],
                                        'times': times,
                                        'values': values,
                                        'labels': labels,
                                        'minNormal': dash_item.minimum_normal_value,
                                        'maxNormal': dash_item.maximum_normal_value,
                                        'minAxis': min(minAxis, min(values)),
                                        'maxAxis': max(maxAxis, max(values)),
                                        'minTime': datetime.fromtimestamp(minTime,tz).strftime('%Y-%m-%d %H:%M:%S'),
                                        'maxTime': datetime.fromtimestamp(maxTime,tz).strftime('%Y-%m-%d %H:%M:%S')
                                       } )

                else:
                    # db_recs = None
                    new_widget['type'] = bmsapp.models.DashboardItem.NOT_CURRENT
                    last_read = dash_item.sensor.sensor.last_read(self.reading_db)
                    cur_value = float(bmsapp.data_util.formatCurVal(last_read['val']).translate(None, ',')) if last_read else None
                    if cur_value is None:
                        new_widget['age'] = 'Not Available'
                    else:
                        age_secs = time.time() - last_read['ts']    # how long ago reading occurred
                        if age_secs < 86400:
                            new_widget['age'] = '%.1f hours Old' % (age_secs/3600.0)
                        elif age_secs >= 86400:
                            new_widget['age'] = '%.1f days Old' % (age_secs/86400.0)
            else:
                # dash_item.sensor = None
                new_widget['type'] = bmsapp.models.DashboardItem.NOT_CURRENT
                new_widget['age'] = 'Not Available'

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


