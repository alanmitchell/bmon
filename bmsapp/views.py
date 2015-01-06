# Create your views here.
import sys, logging, json, random

from django.http import HttpResponse
from django.shortcuts import render_to_response, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.core.urlresolvers import reverse
from django.conf import settings

import models, global_vars, view_util, storereads
from reports import basechart
from readingdb import bmsdata

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

def reports(request, bldg_id=None):
    '''
    The main graphs/reports page.  If 'bldg_id' is the building to be selected;
    if None, the first building in the list is selected.
    '''

    # get the html for the list of building groups and the ID of the selected 
    # group.
    group_html, group_id_selected = view_util.group_list_html()

    # get the html for the list of buildings and the ID of the a selected building
    # (the first building)
    bldgs_html, bldg_id_selected = view_util.bldg_list_html(group_id_selected, view_util.to_int(bldg_id))

    # get the html for the list of charts, selecting the first one.  Returns the actual ID
    # of the chart selected.  The group_id of 0 indicates all buildings are being shown.
    chart_list_html, chart_id_selected = view_util.chart_list_html(0, bldg_id_selected)

    # get the option item html for the list of sensors associated with this building,
    # selecting the first sensor.
    sensor_list_html = view_util.sensor_list_html(bldg_id_selected)

    ctx = base_context()
    ctx.update({'groups_html': group_html, 
                'bldgs_html': bldgs_html, 
                'chart_list_html': chart_list_html,
                'sensor_list_html': sensor_list_html})
    
    return render_to_response('bmsapp/reports.html', ctx)

def get_report_results(request):
    """Method called to return the main content of a particular chart
    or report.
    """
    try:
        # Make the chart object
        chart_obj = basechart.get_chart_object(request.GET)
        result = chart_obj.result()
    
    except:
        _logger.exception('Error in get_report_results')
        result = {'html': 'Error in get_report_results', 'objects': []}

    finally:
        if type(result) is HttpResponse:
            # the chart object directly produced an HttpResponse object
            # so just return it directly.
            return result
        else:
            # if the chart object does not produce an HttpResponse object, then
            # the result from the chart object is assumed to be a JSON object.
            return HttpResponse(json.dumps(result), content_type="application/json")

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

        msg = storereads.store(reading_id, req_data)
        return HttpResponse(msg)

    except:
        _logger.exception('Error Storing Reading for ID=%s: %s' % (reading_id, req_data))
        return HttpResponse(sys.exc_info()[1])

@csrf_exempt    # needed to accept HTTP POST requests from systems other than this one.
def store_readings(request):
    '''
    Stores a set of sensor readings in the sensor reading database.  The readings 
    and store key are in the POST data, encoded in JSON.
    '''

    try:
        # The post data is JSON, so decode it.  Once decoded, it is a dictionary
        # with two keys: 'storeKey' and 'readings'
        req_data = json.loads(request.body)

        # Test for a valid key for storing readings.  Key should be unique for each
        # installation.
        storeKey = req_data['storeKey']
        if storeKey != settings.BMSAPP_STORE_KEY:
            return HttpResponse('Invalid Key')

        msg = storereads.store_many(req_data['readings'])
        return HttpResponse(msg)

    except:
        _logger.exception('Error Storing Reading')
        return HttpResponse(sys.exc_info()[1])

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
        _logger.exception('Error Storing Reading for: %s' %  req_data)
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

def bldg_list(request, group_id):
    '''
    Returns a list of buildings in the group identified by the primary key
    ID of 'group_id'. The 'selected_group' value of 0 means no group 
    selected, so return all buildings.
    
    The return value is an html snippet of option elements, one for each building.
    '''

    bldgs_html, id_selected = view_util.bldg_list_html(int(group_id))

    return HttpResponse(bldgs_html)


def chart_sensor_list(request, group_id, bldg_id):
    '''
    Returns a list of charts and a list of sensors appropriate for a building 
    identified by the primary key ID of 'bldg_id'.  'bldg_id' could be the string 
    'multi', in which case the list of multi-building charts is returned, and 
    only multi-building charts appropriate for the Building Group identified by 
    'group_id' are returned.  A list of sensors appropriate for 'bldg_id' is
    also returned.  If 'bldg_id' is 'multi' then no sensors are returned.
    The return lists are html snippets of option elements.  The two different
    option element lists are returned in a JSON object, with the keys 'charts'
    and 'sensors'.
    '''

    # try to convert the selected building value to an integer (might be the 
    # string 'multi') so that it will match the integer IDs in the database.
    bldg_id = view_util.to_int(bldg_id)
    
    group_id = int(group_id)

    charts_html, id_selected = view_util.chart_list_html(group_id, bldg_id)
    sensor_html = view_util.sensor_list_html(bldg_id)
    result = {'charts': charts_html, 'sensors': sensor_html}

    return HttpResponse(json.dumps(result), content_type="application/json")

def get_readings(request, reading_id):
    """Returns all the rows for one sensor in JSON format.
    'reading_id' is the id of the sensor/reading being requested.
    """

    # open the database 
    db = bmsdata.BMSdata(global_vars.DATA_DB_FILENAME)
    result = db.rowsForOneID(reading_id)

    return HttpResponse(json.dumps(result), content_type="application/json")

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

