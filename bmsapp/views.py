﻿# Create your views here.
import sys, logging, json, random, time

from django.http import HttpResponse
from django.shortcuts import render_to_response, redirect, render
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.core.urlresolvers import reverse
from django.conf import settings
from django.templatetags.static import static

import models
import logging_setup
import view_util
import storereads
from reports import basechart
from readingdb import bmsdata
import periodic_scripts.ecobee

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
    ctx['bmsapp_nav_link_base_url'] = reverse('index')
    return ctx

def index(request):
    '''
    The main home page for the site, which redirects to the desired page to show for the home page.
    '''
    # find the index page in the set of navigation links
    for lnk in TMPL_CONTEXT['bmsapp_nav_links']:
        if len(lnk)==3 and lnk[2]==True:
            return redirect( reverse('wildcard', args=(lnk[1],)) )

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
                'sensor_list_html': sensor_list_html,
                'curtime': int(time.time())})
    
    return render_to_response('bmsapp/reports.html', ctx)

def get_report_results(request):
    """Method called to return the main content of a particular chart
    or report.
    """
    try:
        # Make the chart object
        chart_obj = basechart.get_chart_object(request.GET)
        result = chart_obj.result()
    
    except Exception as e:
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

def get_embedded_results(request):
    """Method called to return the main content of a particular chart
    or report embedded as javascript.
    """
    try:
        # Make the chart object
        chart_obj = basechart.get_chart_object(request.GET)
        result = chart_obj.result()
    
    except Exception as e:
        _logger.exception('Error in get_embedded_results')
        result = {'html': 'Error in get_embedded_results', 'objects': []}

    finally:
        if type(result) is HttpResponse:
            # the chart object directly produced an HttpResponse object
            # so just return it directly.
            return result
        else:
            script_content = '''
(function(){
  var content = json_result_string;

  var scriptTag = document.querySelector(\'script[src="request_path_string"]\');

  var newDiv = document.createElement("div");
  newDiv.innerHTML = content["html"];
  newDiv.style.cssText = scriptTag.style.cssText;
  
  scriptTag.parentElement.replaceChild(newDiv, scriptTag);
'''
            script_content = script_content.replace('json_result_string',json.dumps(result)).replace('request_path_string',request.get_full_path())

            if result["objects"] and result["objects"][0][0] == 'dashboard':
                script_content = 'var loadingDashboard;\n' + script_content
                script_content = 'var loadingPlotly;\n' + script_content
                script_content += '''

  var renderDashboard = (function(){
      // Load the dashboard script if undefined, and add the chart
      if ((typeof ANdash == 'undefined') || (typeof Gauge == 'undefined')) {
          if (!loadingDashboard) {
            loadingDashboard = true;
            console.log('loading dashboard')

            var dashboard_css = document.createElement('link');
            dashboard_css.rel = 'stylesheet';
            dashboard_css.type = 'text/css';
            dashboard_css.href = 'dashboard_css_url';
            document.getElementsByTagName('head')[0].appendChild(dashboard_css);

            var dashboard_script = document.createElement('script');
            dashboard_script.src = 'dashboard_script_url';
            document.getElementsByTagName('head')[0].appendChild(dashboard_script);

            var gauge_script = document.createElement('script');
            gauge_script.src = 'gauge_script_url';
            document.getElementsByTagName('head')[0].appendChild(gauge_script);
          }
          console.log('waiting for dashboard')
          setTimeout(renderDashboard, 100);
      } else if (typeof Plotly == 'undefined') {
          if (!loadingPlotly) {
            console.log('loading plotly')
            loadingPlotly = true;

            var plotly_script = document.createElement('script');
            plotly_script.src = 'https://cdn.plot.ly/plotly-latest.min.js';
            document.getElementsByTagName('head')[0].appendChild(plotly_script);
          }
          console.log('waiting for plotly')
          setTimeout(renderDashboard, 100);
      } else {
        ANdash.createDashboard(obj_config);
      }});
  
  var obj_config = content['objects'][0][1];
  renderDashboard();
'''
                script_content = script_content.replace('dashboard_css_url',request.build_absolute_uri(static('bmsapp/css/dashboard.css')) + '?t=' + str(int(time.time())))
                script_content = script_content.replace('dashboard_script_url',request.build_absolute_uri(static('bmsapp/scripts/dashboard.js')) + '?t=' + str(int(time.time())))
                script_content = script_content.replace('gauge_script_url',request.build_absolute_uri(static('bmsapp/scripts/gauge.min.js')))
            elif result["objects"] and result["objects"][0][0] == 'plotly':
                script_content = 'var loadingPlotly;\n' + script_content
                script_content += '''

  var drawGraph = (function(){
      // Load the Plotly script if undefined, and add the chart
      if (typeof Plotly == 'undefined') {
          if (!loadingPlotly) {
            console.log('loading plotly')
            loadingPlotly = true;

            var plotly_script = document.createElement('script');
            plotly_script.src = 'https://cdn.plot.ly/plotly-latest.min.js';
            document.getElementsByTagName('head')[0].appendChild(plotly_script);
          }
          console.log('waiting for plotly')
          setTimeout(drawGraph, 100);
      } else {
        Plotly.plot(obj_config.renderTo, obj_config.data, obj_config.layout, obj_config.config);
        document.getElementById(obj_config.renderTo).removeAttribute("id");
      }});
  
  var obj_config = content['objects'][0][1];
  drawGraph();
'''

            script_content += '})();' #close the javascript function declaration

            return HttpResponse(script_content, content_type="application/javascript")

def custom_report_list(request):
    '''
    The main Custom Reports page - lists all available custom reports
    '''

    ctx = base_context()
    ctx.update({'customReports': view_util.custom_reports()})
    
    return render_to_response('bmsapp/customReports.html', ctx)

def custom_report(request, requested_report):
    '''
    Display a specific custom report
    '''

    report_title = requested_report

    ctx = base_context()
    ctx.update({'report_title': report_title, 'report_content': view_util.custom_report_html(report_title)})
    
    return render_to_response('bmsapp/customReport.html', ctx)

def store_key_is_valid(the_key):
    '''Returns True if the 'the_key' is a valid sensor reading storage key.
    '''
    if type(settings.BMSAPP_STORE_KEY) in (tuple, list):
        # there are multiple valid storage keys
        return True if the_key in settings.BMSAPP_STORE_KEY else False
    else:
        # there is only one valid storage key
        return the_key==settings.BMSAPP_STORE_KEY


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
        if store_key_is_valid(storeKey):
            msg = storereads.store(reading_id, req_data)
            return HttpResponse(msg)
        else:
            _logger.warning('Invalid Storage Key in Reading Post: %s', storeKey)
            return HttpResponse('Invalid Key')

    except:
        _logger.exception('Error Storing Reading for ID=%s: %s' % (reading_id, req_data))
        return HttpResponse(sys.exc_info()[1])


@csrf_exempt    # needed to accept HTTP POST requests from systems other than this one.
def store_readings(request):
    '''
    Stores a set of sensor readings in the sensor reading database.  The readings
    are in the POST data encoded in JSON and there may be additional information in
    the query string.  See 'storereads.store_many' for details on the data formats
    supported of the request data.
    '''
    try:
        # The post data is JSON, so decode it.
        req_data = json.loads(request.body)

        # Add any query parameters into the dictionary
        req_data.update(request.GET.dict())

        # Test for a valid key for storing readings.  Key should be unique for each
        # installation.
        storeKey = req_data.get('storeKey', 'bad')    # if no storeKey, 'bad' will be returned
        if store_key_is_valid(storeKey):
            # remove storeKey for security
            del(req_data['storeKey'])
            _logger.debug('Sensor Readings: %s' % req_data)
            msg = storereads.store_many(req_data)
            return HttpResponse(msg)
        else:
            _logger.warning('Invalid Storage Key in Reading Post: %s', storeKey)
            return HttpResponse('Invalid Key')

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
    db = bmsdata.BMSdata()
    result = db.rowsForOneID(reading_id)

    return HttpResponse(json.dumps(result), content_type="application/json")

def show_log(request):
    '''
    Returns the application's log file, without formatting.
    '''
    return HttpResponse('<pre>%s</pre>' % open(logging_setup.LOG_FILE).read())

def show_video(request, filename, width, height):
    '''
    A Page to show a training video.  'filename' is the Flash file name of the video, without
    the 'swf' extension, 'width' and 'height' are the width and height in pixels of the viewport.
    A 'hide_back_link' GET parameter is optional; if set to 1, it will hide the 'Back to Video
    List' link on the page.
    '''
    hide_back_link = True if request.GET.get('hide_back_link') == '1' else False

    return render_to_response('bmsapp/video.html', 
        {'filename': filename, 'width': width, 'height': height, 'hide_back_link': hide_back_link})

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

def ecobee_auth(request):
    """Used to generated a form so that a System Admin can obtain access keys
    for reading data from the Ecobee thermostat server.
    """

    ctx = base_context()
    if request.method == 'GET':
        # Get a PIN and auth code
        results = periodic_scripts.ecobee.get_pin()
        ctx.update(results)
        return render(request, 'bmsapp/ecobee_auth.html', ctx)

    elif request.method == 'POST':
        req = request.POST.dict()
        # request access and refresh tokens
        success, access_token, refresh_token = periodic_scripts.ecobee.get_tokens(req['code'])
        ctx.update({'success': success, 'access_token': access_token, 'refresh_token': refresh_token})
        return render_to_response('bmsapp/ecobee_auth_result.html', ctx)

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
