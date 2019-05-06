import numpy as np, pandas as pd, xlwt
from django.http import HttpResponse
import bmsapp.models, bmsapp.data_util
from . import basechart

class ExportData(basechart.BaseChart):
    """Class that exports data as an Excel spreadsheet.
    """

    # see BaseChart for definition of these constants
    CTRLS = 'ctrl_sensor, ctrl_avg_export, time_period_group, download_many'
    MULTI_SENSOR = 1
    AUTO_RECALC = 0

    def result(self):
        """
        Extracts the requested sensor data, averages it, and creates an Excel spreadsheet
        which is then written to an HttpResponse object, which is returned.
        """

        # determine a name for the spreadsheet and fill out the response object
        # headers.
        xls_name = 'sensors_%s.xls' % bmsapp.data_util.ts_to_datetime().strftime('%Y-%m-%d_%H%M%S')
        resp_object = HttpResponse()
        resp_object['Content-Type']= 'application/vnd.ms-excel'
        resp_object['Content-Disposition'] = 'attachment; filename=%s' % xls_name
        resp_object['Content-Description'] = 'Sensor Data - readable in Excel'

        # start the Excel workbook and format the first row and first column
        wb = xlwt.Workbook()
        ws = wb.add_sheet('Sensor Data')
        # column title style
        t1_style = xlwt.easyxf('font: bold on; borders: bottom thin; align: wrap on, vert bottom, horiz center')
        # date formatting style
        dt_style = xlwt.easyxf(num_format_str='M/D/yy  h:mm AM/PM;@')

        ws.write(0, 0, "Timestamp", t1_style)
        ws.col(0).width = 4300

        # get the averaging interval
        averaging_hours = float(self.request_params['averaging_time_export'])

        # walk through sensors, setting column titles and building a Pandas DataFrame
        # that aligns the averaged timestamps of the different sensors.
        col = 1   # tracks spreadsheet column
        df = pd.DataFrame()
        blank_col_names = []   # need to remember columns that have no readings
        for id in self.request_params.getlist('select_sensor_multi'):
            sensor = bmsapp.models.Sensor.objects.get(pk=id)

            # write column heading in spreadsheet
            ws.write(0, col, '%s, %s' % (sensor.title, sensor.unit.label), t1_style)
            ws.col(col).width = 3600

            # determine the start time for selecting records and make a DataFrame from
            # the records
            st_ts, end_ts = self.get_ts_range()
            df_new = self.reading_db.dataframeForOneID(sensor.sensor_id, st_ts, end_ts, self.timezone)
            if not df_new.empty:
                df_new = bmsapp.data_util.resample_timeseries(df_new, averaging_hours)
                df_new.drop('ts', axis=1, inplace=True) # drop the timestamp column
                df_new.rename(columns = {'val': 'col%03d' % col}, inplace = True) # rename the value column

                # join this with the existing DataFrame, taking the union of all timestamps
                df = df.join(df_new, how='outer')
            else:
                # there are no records.  Save this column name to be added at end of join
                # process.  Can't add the column right now because DataFrame may be totally
                # empty, and it doesn't seem possible to add a column to an empty DataFrame.
                blank_col_names.append('col%03d' % col)

            col += 1
        
        # add any blank columns to the dataframe
        for col_name in blank_col_names:
            df[col_name] = np.NaN

        # but now need sort the columns back to order they arrived
        df = df.sort_index(axis=1)

        # put the data in the spreadsheet
        row = 1
        for ix, ser in df.iterrows():
            ws.write(row, 0, ix, dt_style)
            col = 1
            for v in ser.values:
                if not np.isnan(v):
                    ws.write(row, col, v)
                col += 1
            row += 1
            # flush the row data every 1000 rows to save memory.
            if (row % 1000) == 0:
                ws.flush_row_data()

        # Write the spreadsheet to the HttpResponse object
        wb.save(resp_object)
        return resp_object

