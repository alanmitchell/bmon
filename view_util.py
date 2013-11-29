'''
Helper functions for the views in this BMS application.
'''

from django.template import Context, loader
from django.core.urlresolvers import reverse

import models

def to_int(val):
    '''
    Trys to convert 'val' to an integer and returns the integer.  If 'val' is not an integer,
    just returns the original 'val'.
    '''
    try:
        return int(val)
    except:
        return val


def chart_from_id(chart_type, chart_id):
    '''
    Returns a chart object from the application models based on 'chart_type' ('multi' for multi-building charts
    or anything else for one-building charts) and a chart ID 'chart_id'.
    '''

    if chart_type=='multi':
        return models.MultiBuildingChart.objects.get(id=int(chart_id))
    else:
        return models.BuildingChart.objects.get(id=int(chart_id))


def bldg_list_html(selected_bldg=None):
    '''
    Makes the html for the building list options and also returns the ID of the selected building.
    (when 'selected_bldg" is passed in as None, the first building is selected and that ID is returned).
    'selected_bldg' is the ID of the building to select in the option list.  If None, then
        the first building is selected.
    '''
    bldgs = []

    # Determine whether a Multi building chart selection should be presented.
    if models.MultiBuildingChart.objects.count() > 0:
        bldgs.append( ('multi', 'Multiple Buildings') )

    # Add the rest of buildings
    for bldg in models.Building.objects.all():
        bldgs.append( (bldg.id, bldg.title) )

    if selected_bldg==None:
        selected_bldg = bldgs[0][0]    # select first ID

    t = loader.get_template('bmsapp/bldg_list.html')
    return t.render( Context({'bldg_list': bldgs, 'id_to_select': selected_bldg}) ), selected_bldg


def chart_list_html(bldg, selected_chart=None):
    '''
    Makes the html for the chart list options and also returns the ID of the selected chart.
    (which is the passed in 'selected_chart' value, except a real chart ID is returned is 
    selected_chart=None.)
    'bldg' is the ID of the of building to list charts for, or it is the string 'multi'
        indicating that the multi-building charts should be listed.
    'selected_chart' is the ID of the chart option to be selected.  If None,
        the first chart is selected.
    '''
    if bldg != 'multi':
        cht_list = models.BuildingChart.objects.filter(building=bldg)
    else:
        cht_list = models.MultiBuildingChart.objects.all()

    # Determine the chart ID to select
    if selected_chart==None and len(cht_list)>0:
        # select the first chart if selected_chart is None
        id_to_select = cht_list[0].id
    else:
        id_to_select = selected_chart

    t = loader.get_template('bmsapp/chart_list.html')
    return t.render( Context({'cht_list': cht_list, 'id_to_select': id_to_select}) ), id_to_select
