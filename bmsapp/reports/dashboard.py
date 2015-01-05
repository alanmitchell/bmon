class Dashboard(BaseChart):

    def result(self):
        """Create the dashboard HTML and configuration object.
        """

        # open the database 
        db = bmsdata.BMSdata(global_vars.DATA_DB_FILENAME)

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
                last_read = db.last_read(dash_item.sensor.sensor.sensor_id)
                cur_value = float(formatCurVal(last_read['val'])) if last_read else None
                age_secs = time.time() - last_read['ts'] if last_read else None    # how long ago reading occurred
                minAxis, maxAxis = dash_item.get_axis_range()
                new_widget.update( {'units': dash_item.sensor.sensor.unit.label,
                                    'value': cur_value,
                                    'minNormal': dash_item.minimum_normal_value,
                                    'maxNormal': dash_item.maximum_normal_value,
                                    'minAxis': min(minAxis, cur_value),
                                    'maxAxis': max(maxAxis, cur_value),
                                    'timeChartID': TIME_SERIES_CHART_ID,
                                    'sensorID': dash_item.sensor.sensor.id,
                                   } )
                # check to see if data is older than 2 hours or missing, and change widget type if so.
                if cur_value is None:
                    new_widget['type'] = models.DashboardItem.NOT_CURRENT
                    new_widget['age'] = 'Not Available'
                elif 7200 <= age_secs < 86400:
                    new_widget['type'] = models.DashboardItem.NOT_CURRENT
                    new_widget['age'] = '%.1f hours Old' % (age_secs/3600.0)
                elif age_secs >= 86400:
                    new_widget['type'] = models.DashboardItem.NOT_CURRENT
                    new_widget['age'] = '%.1f days Old' % (age_secs/86400.0)

            cur_row.append(new_widget)

        # append the last row if anything is present in that row
        if len(cur_row):
            widgets.append(cur_row)

        # close the reading database
        db.close()

        dash_config = {'widgets': widgets, 'renderTo': 'dashboard'}

        html = '''<h2 id="report_title">%s Dashboard</h2>
        <div id="dashboard" style="background: #FFFFFF"></div>''' % self.building.title

        return {'html': html, 'objects': [('dashboard', dash_config)]}


