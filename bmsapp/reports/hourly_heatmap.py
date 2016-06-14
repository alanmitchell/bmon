import pandas as pd
import bmsapp.models
import bmsapp.data_util
import basechart
import chart_config


class HourlyHeatMap(basechart.BaseChart):
                 }
        opt['tooltip']['pointFormat'] = "<b>{point.value} %s</b>" % (the_sensor.unit.label)

        html = '<div id="chart_container"></div>'

        return {'html': html, 'objects': [('highcharts', opt)]}

