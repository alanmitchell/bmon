# Create your views here.
import sys, logging, json, random, time

import dateutil.parser

from django.http import HttpResponse
from django.shortcuts import render_to_response, redirect, render
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse
from django.conf import settings
from django.templatetags.static import static

from . import models
from . import logging_setup
from . import view_util
from . import storereads
from .reports import basechart
from .readingdb import bmsdata
from bmsapp.periodic_scripts import ecobee
import bmsapp.scripts.backup_readingdb

# Make a logger for this module
_logger = logging.getLogger('bms.' + __name__)

# Some context variables to include when rendering all templates
DEFAULT_NAV_LINKS = ( ('Data Charts and Reports', 'reports', True),
                      ('Training Videos and Project Reports', 'training-anthc'),
                    )

TMPL_CONTEXT = {'bmsapp_title_text': getattr(settings, 'BMSAPP_TITLE_TEXT', 'Facility Monitoring'),
                'bmsapp_header': getattr(settings, 'BMSAPP_HEADER', 'Facility Monitoring'),
                'bmsapp_footer': getattr(settings, 'BMSAPP_FOOTER', 'Thanks to Alaska Housing Finance Corporation for providing most of the source code for this application.'),
                'bmsapp_nav_links': getattr(settings, 'BMSAPP_NAV_LINKS', DEFAULT_NAV_LINKS),
                'version_date': view_util.version_date_string(),
               }

def base_context():
    '''
    Returns a Template rendering context with some basic variables.
    Had to do this because I could not run the 'reverse' method from the module level.
    '''
    # get the html for the list of organizations and ID of the selected
    # organization.
    orgs_html, _ = view_util.organization_list_html()
    
    # determine whether organization selector should be hidden based on how 
    # many options there are in the select drop down.
    orgs_hide = (orgs_html.count('value') == 1)

    ctx = TMPL_CONTEXT.copy()
    ctx['orgs_html'] = orgs_html
    ctx['orgs_hide'] = orgs_hide
    ctx['bmsapp_nav_link_base_url'] = reverse('index')

    # Only show Logout button if Django Lockdown app is being used.
    ctx['logout_show'] = ('lockdown' in settings.INSTALLED_APPS)

    return ctx

def index(request):
    '''
    The main home page for the site, which redirects to the desired page to show for the home page.
    '''
    # find the index page in the set of navigation links
    for lnk in TMPL_CONTEXT['bmsapp_nav_links']:
        if len(lnk)==3 and lnk[2]==True:
            return redirect( reverse('wildcard', args=(lnk[1],)) )

def reports(request):
    '''
    The main graphs/reports page.  If 'bldg_id' is the building to be selected;
    if None, the first building in the list is selected.
    '''

    # get the html for the list of building groups and the ID of the selected 
    # group.
    group_html, group_id_selected = view_util.group_list_html(0)

    # get the html for the list of buildings and the ID of the a selected building
    # (the first building)
    bldgs_html, bldg_id_selected = view_util.bldg_list_html(0, group_id_selected, None)

    # get the html for the list of charts, selecting the first one.  Returns the actual ID
    # of the chart selected.  The org_id of 0 indicates all organizations are being shown.
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
        chart_obj = basechart.get_chart_object(request)
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
    """Method called to return the main content of a particular chart or report
       embedded as javascript.
    """
    try:
        # Make the chart object
        chart_obj = basechart.get_chart_object(request)
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
            script_content = view_util.get_embedded_results_script(request, result)
            return HttpResponse(script_content, content_type="application/javascript")

def energy_reports(request):
    """Presents the BMON Essential Energy Reports page.
    """
    # determine the base Energy Reports URL to pass to the template
    if hasattr(settings, 'ENERGY_REPORTS_URL') and settings.ENERGY_REPORTS_URL is not None:
        energy_reports_url = settings.ENERGY_REPORTS_URL
        if energy_reports_url[-1] != '/':
            # add a slash at end, as it did not contain one.
            energy_reports_url += '/'
        error_message = ''
    else:
        energy_reports_url = ''
        error_message = 'Energy Reports are not Available.  Contact your System Administrator for more information.'

    ctx = base_context()
    ctx.update(
        {
            'energy_reports_url': energy_reports_url,
            'error_message': error_message,
        }
    )
    
    return render_to_response('bmsapp/energy-reports.html', ctx)

def custom_report_list(request):
    """The main Custom Reports page - lists available custom reports for the
    organization identified by the query parameter 'select_org'.
    """
    org_id = int(request.GET.get('select_org', '0'))
    ctx = base_context()
    ctx.update({
        'org_id': org_id,
        'customReports': view_util.custom_reports(org_id)
        })
    
    return render_to_response('bmsapp/customReports.html', ctx)

def custom_report(request, requested_report):
    '''
    Display a specific custom report
    '''

    report_id = requested_report
    ctx = base_context()

    try:
        report = models.CustomReport.objects.get(id=report_id)
        report_title = report.title
        ctx.update({'report_title': report_title, 'report_content': view_util.custom_report_html(report_id)})
    except Exception as ex:
        ctx.update({'report_title': 'Report Not Found', 'report_content': 'Report Not Found: ' + ex.message})
    
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

@csrf_exempt    # needed to accept HTTP POST requests from systems other than this one.
def store_readings_things(request):
    '''
    Stores a set of sensor readings from the Things Network in the sensor reading 
    database. The readings are assumed to originate from an HTTP Integration on an
    Application in the Things Network.  The BMON Store Key is in a custom HTTP header.
    The readings and other data are in the POST data encoded in JSON.
    '''

    # Payload Fields from Things Network nodes that do not contain sensor
    # readings.
    EXCLUDE_THINGS_FIELDS = ('event', )

    try:

        # The post data is JSON, so decode it.
        req_data = json.loads(request.body)

        # Return if this is a message that does not have any data in it, like an 
        # activate or join message.
        if 'payload_fields' not in req_data:
            return HttpResponse('No Data')

        # See if the store key is valid.  It's stored in the "store-key" header, which
        # is found in the "HTTP_STORE_KEY" key in the META dictionary.
        storeKey = request.META.get('HTTP_STORE_KEY', 'None_Present')

        if store_key_is_valid(storeKey):
            readings = []
            ts = dateutil.parser.parse(req_data['metadata']['time']).timestamp()
            hdw_serial = req_data['hardware_serial']
            for fld, val in req_data['payload_fields'].items():
                if fld not in EXCLUDE_THINGS_FIELDS:
                    readings.append( [ts, f'{hdw_serial}_{fld}', val] )

            # Also extract the SNR and RSSI received by gateway that received this
            # message and had the best SNR.
            sigs = [(gtw['snr'], gtw['rssi']) for gtw in req_data['metadata']['gateways']]
            snr, rssi = max(sigs)
            readings.append([ts, f'{hdw_serial}_snr', snr])
            readings.append([ts, f'{hdw_serial}_rssi', rssi])

            msg = storereads.store_many({'readings': readings})

            return HttpResponse(msg)
        else:
            _logger.warning('Invalid Storage Key in Reading Post: %s', storeKey)
            return HttpResponse('Invalid Key')

    except:
        _logger.exception('Error Storing Reading')
        return HttpResponse(sys.exc_info()[1])

@csrf_exempt    # needed to accept HTTP POST requests from systems other than this one.
def store_readings_radio_bridge(request):
    '''
    Stores a set of sensor readings from a Radio Bridge LoRaWAN sensor in the sensor reading 
    database. The readings are assumed to originate from an HTTP Integration on an
    Application in the Things Network.  The BMON Store Key is in a custom HTTP header.
    The readings and other data are in the POST data encoded in JSON.
    '''

    try:

        # The post data is JSON, so decode it.
        req_data = json.loads(request.body)

        # Return if this is a message that does not have any data in it, like an 
        # activate or join message.
        if 'payload_fields' not in req_data:
            return HttpResponse('No Data')

        # See if the store key is valid.  It's stored in the "store-key" header, which
        # is found in the "HTTP_STORE_KEY" key in the META dictionary.
        storeKey = request.META.get('HTTP_STORE_KEY', 'None_Present')

        if store_key_is_valid(storeKey):
            readings = []
            ts = dateutil.parser.parse(req_data['metadata']['time']).timestamp()
            hdw_serial = req_data['hardware_serial']

            pf = req_data['payload_fields']
            event = pf['EVENT_TYPE']
            if event == '01':     # Supervisory Event
                readings.append( [ts, f'{hdw_serial}_battery', float(pf['BATTERY_LEVEL'])] )

            elif event == '07':    # Contact event
                val = float(pf['SENSOR_STATE'])
                # Invert their logic: they have a 0 when the contacts are closed
                val = val * -1 + 1
                readings.append( [ts, f'{hdw_serial}_state', val] )

            elif event == '09':   # Temperature Event
                readings.append( [ts, f'{hdw_serial}_temp', pf['TEMPERATURE'] * 1.8 + 32.] )

            else:
                return HttpResponse('No Data')

            msg = storereads.store_many({'readings': readings})

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

def group_list(request, org_id):
    """Returns a list of building groups associated with the organization identified
    by 'org_id'.  The return value is an html snippet of option elements, one
    for each building group.
    """
    group_html, _ = view_util.group_list_html(int(org_id))

    return HttpResponse(group_html)

def bldg_list(request, org_id, group_id):
    '''Returns a list of buildings in the organization identified by 'org_id'
    and the group identified by the primary key ID of 'group_id'. 

    The return value is an html snippet of option elements, one for each building.
    '''

    bldgs_html, _ = view_util.bldg_list_html(int(org_id), int(group_id))

    return HttpResponse(bldgs_html)

def chart_sensor_list(request, org_id, bldg_id):
    '''
    Returns a list of charts and a list of sensors appropriate for a building
    identified by the primary key ID of 'bldg_id'.  'bldg_id' could be the string
    'multi', in which case the list of multi-building charts is returned, and
    only multi-building charts appropriate for the Organization identified by
    'org_id' are returned.  A list of sensors appropriate for 'bldg_id' is
    also returned.  If 'bldg_id' is 'multi' then no sensors are returned.
    The return lists are html snippets of option elements.  The two different
    option element lists are returned in a JSON object, with the keys 'charts'
    and 'sensors'.
    '''

    # try to convert the selected building value to an integer (might be the 
    # string 'multi') so that it will match the integer IDs in the database.
    bldg_id = view_util.to_int(bldg_id)
    
    org_id = int(org_id)

    charts_html, id_selected = view_util.chart_list_html(org_id, bldg_id)
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

@login_required(login_url='../admin/login/')
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
    ret = {"name": "BMON Sites",
        "type": "FeatureCollection",
        "crs": {"type": "name", "properties": {"name": "urn:ogc:def:crs:OGC:1.3:CRS83"}},
        "features": []}

    org_id = int(request.GET.get('select_org', '0'))
    if org_id != 0:
        bldgs = models.Organization.objects.get(id=org_id).buildings.all()
    else:
        bldgs = models.Building.objects.all()

    for bldg in bldgs:
        ret['features'].append( {"type": "Feature", 
                                 "geometry": {"type": "Point", 
                                              "coordinates": [bldg.longitude, bldg.latitude]
                                              },
                                 "properties": {"facilityName": bldg.title, 
                                                "facilityID": bldg.id, 
                                                "message": "", 
                                                "href": '{}?select_org={}&select_bldg={}'.format(request.build_absolute_uri('../reports/'), org_id, bldg.id)
                                                }
                                 } )


    return HttpResponse(json.dumps(ret), content_type="application/json")

@login_required(login_url='../admin/login/')
def ecobee_auth(request):
    """Used to generated a form so that a System Admin can obtain access keys
    for reading data from the Ecobee thermostat server.
    """

    ctx = base_context()
    if request.method == 'GET':
        # Get a PIN and auth code
        results = ecobee.get_pin()
        ctx.update(results)
        return render(request, 'bmsapp/ecobee_authorization.html', ctx)

    elif request.method == 'POST':
        req = request.POST.dict()
        # request access and refresh tokens
        success, access_token, refresh_token = ecobee.get_tokens(req['code'])
        ctx.update({'success': success, 'access_token': access_token, 'refresh_token': refresh_token})
        return render_to_response('bmsapp/ecobee_auth_result.html', ctx)

@login_required(login_url='../admin/login/')
def unassigned_sensors(request):
    """Shows sensors that are in the Reading Database but not assigned to a building.
    """

    db = bmsdata.BMSdata()
    sensor_list = []
    for sens_id in db.sensor_id_list():
        sensor_info = {'id': sens_id, 'title': '', 'cur_value': '', 'minutes_ago': ''}
        add_sensor = False

        qs = models.Sensor.objects.filter(sensor_id=sens_id)
        if len(qs)==0:
            # Sensor does not even have a sensor object
            add_sensor = True
        else:
            sensor = qs[0]   # get the actual Sensor object
            # see if this sensor has links to a building
            links = models.BldgToSensor.objects.filter(sensor=sensor)
            if len(links)==0:
                # no links, so found an unassigned sensor
                add_sensor = True
                sensor_info['title'] = sensor.title

        if add_sensor:
            last_read = db.last_read(sens_id)
            if last_read:
                val = last_read['val']
                sensor_info['cur_value'] = '%.5g' % val if abs(val)<1e5 else str(val)
                sensor_info['minutes_ago'] = '%.1f' % ((time.time() - last_read['ts'])/60.0)

            sensor_list.append(sensor_info)

    ctx = base_context()
    ctx.update({'sensor_list': sensor_list})
    return render_to_response('bmsapp/unassigned-sensors.html', ctx)

@login_required(login_url='../admin/login/')
def backup_reading_db(request):
    """Causes a backup of the sensor reading database to occur.
    """
    bmsapp.scripts.backup_readingdb.run()
    return HttpResponse('Sensor Reading Backup Complete!')

def wildcard(request, template_name):
    '''
    Used if a URL component doesn't match any of the predefied URL patterns.  Renders
    the template indicated by template_name, adding an '.html' to the name.
    '''
    return render_to_response('bmsapp/%s.html' % template_name, base_context())

@login_required(login_url='../admin/login/')
def password_change_done(request):
    return render_to_response('registration/password_change_done.html',
        {'user': request.user})
