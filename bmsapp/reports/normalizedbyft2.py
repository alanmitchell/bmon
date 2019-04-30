
import yaml
import bmsapp.models, bmsapp.data_util
from . import basechart

class NormalizedByFt2(basechart.BaseChart):
    """
    Chart that normalizes a quantity by floor area.  The value being normalized is first averaged
    over the requested time period and then divided by floor area.  A scaling multiplier is optionally
    applied to the result.

    CHART PARAMETERS:
        'value_units': the units, for example 'kWh/year', to label the Y-axis with; '/ft2'
            will be appended to this value.
        'multiplier' (optional, defaults to 1.0): a scaling multiplier that will be applied to 
            the final value for a building.

    BUILDING PARAMETERS:
        'id_value': the sensor ID of the quantity to sum up and normalize.
        'floor_area': the floor area in square feet of the building.
    """
    
    # see BaseChart for definition of these constants
    CTRLS = 'refresh, time_period_group'
    
    def result(self):
        """
        Returns the HTML and chart configuration for a chart that normalizes a value 
        by floor area.
        """

        # get the time range  used in the analysis
        st_ts, end_ts = self.get_ts_range()

        # get the scaling multiplier if present in the parameters
        multiplier = self.chart_params.get('multiplier', 1.0)

        # start a list of building names and energy use values
        bldg_names = []
        values = []

        # get the buildings in the current building group
        group_id = int(self.request_params['select_group'])
        bldgs = bmsapp.view_util.buildings_for_group(group_id)
        
        # loop through the buildings determining the value per ft2 for each building
        for bldg_info in self.chart_info.chartbuildinginfo_set.filter(building__in=bldgs):

            bldg_name = bldg_info.building.title   # get the building name

            # get the parameters associated with this building
            bldg_params = yaml.load(bldg_info.parameters, Loader=yaml.FullLoader)

            # get the value records
            db_recs = self.reading_db.rowsForOneID(bldg_params['id_value'], st_ts, end_ts)
            if len(db_recs)==0:
                continue

            # make sure the data spans at least 80% of the requested interval.
            # if not, skip this building.
            actual_span = db_recs[-1]['ts'] - db_recs[0]['ts']
            if actual_span / float(end_ts - st_ts) < 0.8:
                continue

            # make a list of the values
            val_list = [rec['val'] for rec in db_recs]
            ct = len(val_list)
            if ct > 0:
                normalized_val = sum(val_list) / float(ct) / bldg_params['floor_area'] * multiplier
                bldg_names.append(bldg_name)
                values.append( round( normalized_val, 2) )

        opt = self.get_chart_options()
        opt['data'] = [{
                        'x': bldg_names,
                        'y': values,
                        'type': 'bar'
                        }]
        opt['layout']['showlegend'] = False
        opt['layout']['yaxis']['title'] =  self.chart_params["value_units"] + '/ft2'
        opt['layout']['yaxis']['rangemode'] = 'tozero'
        opt['layout']['xaxis']['title'] =  ''
        opt['layout']['xaxis']['tickangle'] = -45
        opt['layout']['margin']['b'] = 120           

        '''
        opt['xAxis']['labels'] = {
                    'align': 'right',
                    'style': {'fontSize': '13px'}
                    }
        '''

        html = basechart.chart_config.chart_container_html(opt['layout']['title'])

        return {'html': html, 'objects': [('plotly', opt)]}
