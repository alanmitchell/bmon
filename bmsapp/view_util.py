'''
Helper functions for the views in this BMS application.
'''

from django.template import Context, loader

import models, charts

def to_int(val):
    '''
    Trys to convert 'val' to an integer and returns the integer.  If 'val' is not an integer,
    just returns the original 'val'.
    '''
    try:
        return int(val)
    except:
        return val


def buildings_for_group(group_id):
    """Returns a list of building objects that are in the group identified by 
    'group_id'.  A group_id of 0 indicates All Buildings.
    """

    return models.Building.objects.all() if group_id==0 else \
        models.Building.objects.filter(buildinggroup__pk=group_id)


def multi_charts_for_group(group_id):
    """Returns a list of MultiBuildingChart objects where each chart 
    applies to at least one of the buildings in the Building Group identified
    by group_id.
    """
    
    # a set to hold the multi charts found
    found_charts = set()
    
    # For each building, add its relevant charts to the set
    for bldg in buildings_for_group(group_id):
        found_charts.update( models.MultiBuildingChart.objects.filter(chartbuildinginfo__building__pk=bldg.id) )
    
    # return this as a list, sorted by the sort_order field
    return sorted(found_charts, key=lambda x: x.sort_order)
    

def group_list_html():
    """Returns the html for the building group list options and also returns the
    ID of the first group, which is selected.
    """
    # always have the All Buildings option, which has the special id of 0.
    groups = [ (0, 'All Facilities') ]  
    
    # add the rest of the groups.
    for gp in models.BuildingGroup.objects.all():
        groups.append( (gp.id, gp.title) )
        
    # Selected group is the first one
    selected_gp = groups[0][0]
    
    t = loader.get_template('bmsapp/select_list.html')
    return t.render( Context({'item_list': groups, 'id_to_select': selected_gp}) ), selected_gp


def bldg_list_html(bldg_group_id, selected_bldg_id=None):
    '''
    Makes the html for the building list options and also returns the ID of the 
    building that is selected.  'bldg_group_id' is the primary key
    ID of the building group that filters the building list.  A pk=0 means
    that All buildings are to be included.
    If 'selected_bldg_id' is not None, that building is selected in the list, 
    otherwise the first building in the list is selected.
    '''
    bldgs = []

    # Determine whether a Multi building chart selection should be presented.
    if len(multi_charts_for_group(bldg_group_id)):
        bldgs.append( ('multi', 'Multiple Buildings') )

    # Add the rest of buildings that are in the group
    for bldg in buildings_for_group(bldg_group_id):
        bldgs.append( (bldg.id, bldg.title) )

    if selected_bldg_id==None:
        selected_bldg_id = bldgs[0][0] 

    t = loader.get_template('bmsapp/select_list.html')
    return t.render( Context({'item_list': bldgs, 'id_to_select': selected_bldg_id}) ), selected_bldg_id


def chart_list_html(group_id, bldg_id):
    '''
    Makes the html for the chart list options and also returns the ID of the 
    selected chart, which is the first chart in the list.
    'bldg_id' is the ID of the of building to list charts for, or it is the string 
        'multi' indicating that the multi-building charts should be listed.
    'group_id' is the ID of the building group currently in effect.  If 'bldg_id'
    is 'multi', only multi-building charts relevant to 'group_id' are shown.
    '''
    if bldg_id != 'multi':
        # check to see if there are any Dashboard items
        bldg_object = models.Building.objects.get(id=bldg_id)
        if len(bldg_object.dashboarditem_set.all()):
            # include Dashboard in chart list
            cht_list = charts.BLDG_CHART_TYPES
        else:
            # exclude Dashboard chart.
            cht_list = charts.BLDG_CHART_TYPES[:]  # All items
            for cht in cht_list:
                if cht.class_name == 'Dashboard':
                    cht_list.remove(cht)
                    break
    else:
        cht_list = multi_charts_for_group(group_id)

    # Get the id of the first chart in the list and also make a generic
    # item list.
    id_to_select = cht_list[0].id
    item_list = [ (cht.id, cht.title) for cht in cht_list ]

    t = loader.get_template('bmsapp/select_list.html')
    return t.render( Context({'item_list': item_list, 'id_to_select': id_to_select}) ), id_to_select
