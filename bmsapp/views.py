# Create your views here.
import sys, logging, json, random

from django.http import HttpResponse
from django.shortcuts import render_to_response, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.core.urlresolvers import reverse
from django.conf import settings

import models, global_vars, charts, view_util, storereads

# Make a logger for this module
_logger = logging.getLogger('bms.' + __name__)

# Some context variables to include when rendering all templates
DEFAULT_NAV_LINKS = ( ('Data Charts and Reports', 'reports', True),
                      ('Training Videos and Project Reports', 'training_anthc'),
                    )

TMPL_CONTEXT = {'bmsapp_title_text': getattr(settings, 'BMSAPP_TITLE_TEXT', 'Facility Monitoring'),
                'bmsapp_header': getattr(settings, 'BMSAPP_HEADER', 'Facility Monitoring'),
                'bmsapp_footer': getattr(settings, 'BMSAPP_FOOTER', 'Thanks to Alaska Housing Finance Corporation for providing most of the source code for this application.'),
                'bmsapp_nav_links': getattr(settings, 'BMSAPP_NAV_LINKS', DEFAULT_NAV_LINKS),
               }

def base_context():
    '''
    Returns a Template rendering context with some basic variables.
    Had to do this because I could not run the 'reverse' method from the module level.
    '''
    ctx = TMPL_CONTEXT.copy()
    ctx['bmsapp_nav_link_base_url'] = reverse('bmsapp.views.index')
    return ctx

def index(request):
    '''
    The main home page for the site, which redirects to the desired page to show for the home page.
    '''
    # find the index page in the set of navigation links
    for lnk in TMPL_CONTEXT['bmsapp_nav_links']:
        if len(lnk)==3 and lnk[2]==True:
            return redirect( reverse('bmsapp.views.wildcard', args=(lnk[1],)) )

def reports(request, selected_bldg=None, selected_chart=None, selected_sensor=None):
    '''
    The main graphs/reports page.
    '''

    # try to convert the selected building value to an integer (might be the string 'multi' or None) so that
    # it will match the integer IDs in the database.
    selected_bldg = view_util.to_int(selected_bldg)

    # get the html for the list of buildings and the ID of the a selected building (converts a None
    # into the ID of the first item).
    bldgs_html, bldg_id_selected = view_util.bldg_list_html(selected_bldg)

    # try to convert selected chart to an integer
    selected_chart = view_util.to_int(selected_chart)

    # get the html for the list of charts, selecting the requested one.  Also returns the actual ID
    # of the chart selected (a selected_chart=None is converted to an actual ID).
    chart_list_html, chart_id_selected = view_util.chart_list_html(bldg_id_selected, selected_chart)

    # get the html for configuring and displaying this particular chart
    chart_obj = charts.get_chart_object(bldg_id_selected, chart_id_selected, request.GET)
    chart_html = chart_obj.html(selected_sensor)

    ctx = base_context()
    ctx.update({'bldgs_html': bldgs_html, 'chart_list_html': chart_list_html, 'chart_html': chart_html})
    return render_to_response('bmsapp/reports.html', ctx)

@csrf_exempt    # needed to accept HTTP POST requests from systems other than this one.
def store_reading(request, reading_id):
    '''
    Stores a sensor or calculated reading in the sensor reading database.  'reading_id' is the ID of the
    reading to store.  Other information about the reading is in the GET parameter or POST data of the
    request.
    '''

    try:
        # determine whether request was a GET or POST and extract data
        req_data = request.GET.dict() if request.method == 'GET' else request.POST.dict()

        # Test for a valid key for storing readings.  Key should be unique for each
        # installation.
        storeKey = req_data['storeKey']
        del req_data['storeKey']    # for safety, get the key out of the dictionary
        if storeKey != settings.BMSAPP_STORE_KEY:
            return HttpResponse('Invalid Key')

        storereads.store(reading_id, req_data)
        return HttpResponse('OK')

    except:
        _logger.exception('Error Storing Reading for ID=%s: %s' % (reading_id, req_data))
        return HttpResponse('Error Storing Reading')

@csrf_exempt
def store_reading_old(request, store_key):
    '''
    Stores a reading that uses an older URL pattern.
    '''

    try:
        if store_key == settings.BMSAPP_STORE_KEY_OLD:

            # determine whether request was a GET or POST and extract data
            req_data = request.GET.dict() if request.method == 'GET' else request.POST.dict()

            # pull the reading id out of the request parameters
            reading_id = req_data['id']

            storereads.store(reading_id, req_data)
            return HttpResponse('OK')

        else:
            return HttpResponse('Invalid Key')

    except:
        _logger.exception('Error Storing Reading for: %s' %  data)
        return HttpResponse('Error Storing Reading')

def make_store_key(request):
    '''
    Makes a random 12 character store key
    '''
    k = ''
    for i in range(12):
        val = random.randint(0, 61)
        if val > 35:
            val += 61
        elif val > 9:
            val += 55
        else:
            val += 48
        k += chr(val)

    return HttpResponse(k)

def chart_list(request, selected_bldg):
    '''
    Returns a list of charts appropriate for a building identified by the primary key
    ID of 'selected_bldg'.  'selected_bldg' could be the string 'multi', in which case
    the list of multi-building charts is returned.
    The return value is an html snippet of option elements, one for each chart.
    '''

    # try to convert the selected building value to an integer (might be the string 'multi') so that
    # it will match the integer IDs in the database.
    selected_bldg = view_util.to_int(selected_bldg)

    charts_html, id_selected = view_util.chart_list_html(selected_bldg)

    return HttpResponse(charts_html)


def chart_info(request, bldg_id, chart_id, info_type):
    '''
    Returns the HTML or data needed to display a chart
    'bldg_id' is either the primary key ID (pk) for a chart associated with one building,
    or 'multi', indicating that the chart is for a group of buildings (multi). 
    'chart_id' is the pk ID of the chart requested.
    'info_type' is the type of chart information requested: 'html' to request the HTML for
    the chart page, 'data' to request the data for the chart, or the name of a method on the 
    created chart class to call to return data.
    '''

    try:

        # Make the chart object
        chart_obj = charts.get_chart_object(view_util.to_int(bldg_id), view_util.to_int(chart_id), request.GET)

        # Return the type of data indicated by 'info_type'
        if info_type=='html':
            return HttpResponse(chart_obj.html())

        elif info_type=='data':
            result = chart_obj.data()
            return HttpResponse(json.dumps(result), content_type="application/json")

        else:
            # the 'info_type' indicates the method to call on the object
            the_method = getattr(chart_obj, info_type)

            # give this method an empty response object to fill out and return
            return the_method(HttpResponse())

    except:
        _logger.exception('Error in chart_info')
        return HttpResponse('Error in chart_info')

def show_log(request):
    '''
    Returns the application's log file, without formatting.
    '''
    return HttpResponse('<pre>%s</pre>' % open(global_vars.LOG_FILE).read())

def show_video(request, filename, width, height):
    '''
    A Page to show a training video.  'filename' is the Flash file name of the video, without
    the 'swf' extension, 'width' and 'height' are the width and height in pixels of the viewport.
    '''

    return render_to_response('bmsapp/video.html', {'filename': filename, 'width': width, 'height': height}) 

def map_json(request):
    """Returns the JSON data necessary to draw the Google map of the sites.
    This view is called from the map.html template.
    """
    ret = {"name": "ANTHC_Sites", 
        "type": "FeatureCollection", 
        "crs": {"type": "name", "properties": {"name": "urn:ogc:def:crs:OGC:1.3:CRS83"}},
        "features": []}

    for bldg in models.Building.objects.all():
        ret['features'].append( {"type": "Feature", "geometry": {"type": "Point", "coordinates": [bldg.longitude, bldg.latitude]},
                              "properties": {"facilityName": bldg.title, "facilityID": bldg.id, "message": ""}} )


    return HttpResponse(json.dumps(ret), content_type="application/json")

def wildcard(request, template_name):
    '''
    Used if a URL component doesn't match any of the predefied URL patterns.  Renders
    the template indicated by template_name, adding an '.html' to the name.
    '''
    return render_to_response('bmsapp/%s.html' % template_name, base_context())

@login_required
def password_change_done(request):
    return render_to_response('registration/password_change_done.html',
        {'user': request.user})

