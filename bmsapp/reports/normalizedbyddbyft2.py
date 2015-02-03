import pandas as pd
import yaml
import bmsapp.models, bmsapp.data_util
import basechart

class NormalizedByDDbyFt2(basechart.BaseChart):
    """
    Chart that normalizes a quantity by degree-days and floor area.  Value being normalized
    must be a rate per hour quantity; the normalization integrates by the hour.  For example
    a Btu/hour value integrates to total Btus in this chart.

    CHART PARAMETERS:
        'base_temp': the base temperature in degrees F to use in the degree-day calculation.
        'value_units': the units, for example 'Btus', to label the Y-axis with; '/ft2/degree-day'
            will be appended to this value.
        'multiplier' (optional, defaults to 1.0): a scaling multiplier that will be applied to 
            the final value for a building.

    BUILDING PARAMETERS:
        'id_value': the sensor ID of the quantity to sum up and normalize.
        'id_out_temp': the sensor ID of an outdoor temperature measurement used to calculate
            degree-days.
        'floor_area': the floor area in square feet of the building.
    """
    
    def result(self):
        """
        Returns the HTML & chart objects for a chart that normalizes a value by 
        degree-days and floor area.
        """

        # get the time range  used in the analysis
        st_ts, end_ts = self.get_ts_range()

        # make a timestamp binning object to bin the data into 1 hour intervals
        binner = bmsapp.data_util.TsBin(1.0)

        # get the base temperature for degree day calculations
        base_temp = self.chart_params['base_temp']

        # get the scaling multiplier if present in the parameters
        multiplier = self.chart_params.get('multiplier', 1.0)

        # start a list of building names and energy use values
        bldg_names = []
        values = []

        # get the buildings in the current building group
        group_id = int(self.request_params['select_group'])
        bldgs = bmsapp.view_util.buildings_for_group(group_id)
        
        # loop through the buildings determining the Btu/ft2/dd for each building
        for bldg_info in self.chart_info.chartbuildinginfo_set.filter(building__in=bldgs):

            bldg_name = bldg_info.building.title   # get the building name

            # get the parameters associated with this building
            bldg_params = yaml.load(bldg_info.parameters)

            # get the value records and average into one hour intervals
            db_recs = self.reading_db.rowsForOneID(bldg_params['id_value'], st_ts, end_ts)
            if len(db_recs)==0:
                continue
            df = pd.DataFrame(db_recs).set_index('ts')
            df.columns = ['value']
            df = df.groupby(binner.bin).mean()    # do one hour averaging

            # get outdoor temp data and average into one hour intervals.  
            db_recs = self.reading_db.rowsForOneID(bldg_params['id_out_temp'], st_ts, end_ts)
            if len(db_recs)==0:
                continue
            df_temp = pd.DataFrame(db_recs).set_index('ts')
            df_temp.columns = ['temp']
            df_temp = df_temp.groupby(binner.bin).mean()    # do one hour averaging

            # inner join, matching timestamps
            df = df.join(df_temp, how='inner') 
            
            # make sure the data spans at least 80% of the requested interval.
            # if not, skip this building.
            actual_span = df.index[-1] - df.index[0]
            if actual_span / float(end_ts - st_ts) < 0.8:
                continue

            # calculate total degree-days; each period is an hour, so need to divide by
            # 24.0 at end.
            total_dd = sum([max(base_temp - t, 0.0) for t in df['temp'].values]) / 24.0

            # calculate total of the values and apply the scaling multiplier
            total_values = df['value'].sum() * multiplier

            # if there are any degree-days, append a new point to the list
            if total_dd > 0.0:
                bldg_names.append(bldg_name)
                values.append( round(total_values / total_dd / bldg_params['floor_area'], 2) )

        opt = self.get_chart_options()
        opt['chart']['type'] =  'column'
        opt['legend']['enabled'] = False
        opt['series'] = [{'data': values}]
        opt['xAxis']['categories'] = bldg_names
        opt['yAxis']['title']['text'] = self.chart_params["value_units"] + '/ft2/degree-day'
        opt['yAxis']['min'] = 0
        opt['xAxis']['labels'] = {
                    'rotation': -45,
                    'align': 'right',
                    'style': {'fontSize': '13px'}
                    }

        html = '<div id="chart_container"></div>'

        return {'html': html, 'objects': [('highcharts', opt)]}

