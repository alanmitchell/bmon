# Create your views here.
import sys
import logging
import json
import random
import time
import xml.etree.ElementTree as ET

import dateutil.parser

from django.http import HttpResponse
from django.shortcuts import render_to_response, redirect, render
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse
from django.conf import settings
from django.templatetags.static import static
from django.template import loader

from . import models
from . import logging_setup
from . import view_util
from . import storereads
from .reports import basechart
from .readingdb import bmsdata
from bmsapp.periodic_scripts import ecobee
import bmsapp.scripts.backup_readingdb
from .lora import decoder
from . import notehub

# Make a logger for this module
_logger = logging.getLogger('bms.' + __name__)

# Some context variables to include when rendering all templates
DEFAULT_NAV_LINKS = (('Data Charts and Reports', 'reports', True),
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
        if len(lnk) == 3 and lnk[2] == True:
            return redirect(reverse('wildcard', args=(lnk[1],)))


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
    bldgs_html, bldg_id_selected = view_util.bldg_list_html(
        0, group_id_selected, None)

    # get the html for the list of charts, selecting the first one.  Returns the actual ID
    # of the chart selected.  The org_id of 0 indicates all organizations are being shown.
    chart_list_html, chart_id_selected = view_util.chart_list_html(
        0, bldg_id_selected)

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
            script_content = view_util.get_embedded_results_script(
                request, result)
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
        ctx.update({'report_title': report_title,
                    'report_content': view_util.custom_report_html(report_id)})
    except Exception as ex:
        ctx.update({'report_title': 'Report Not Found',
                    'report_content': 'Report Not Found: ' + ex.message})

    return render_to_response('bmsapp/customReport.html', ctx)


def store_key_is_valid(the_key):
    '''Returns True if the 'the_key' is a valid sensor reading storage key.
    '''
    if type(settings.BMSAPP_STORE_KEY) in (tuple, list):
        # there are multiple valid storage keys
        return True if the_key in settings.BMSAPP_STORE_KEY else False
    else:
        # there is only one valid storage key
        return the_key == settings.BMSAPP_STORE_KEY


# needed to accept HTTP POST requests from systems other than this one.
@csrf_exempt
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
        # for safety, get the key out of the dictionary
        del req_data['storeKey']
        if store_key_is_valid(storeKey):
            msg = storereads.store(reading_id, req_data)
            return HttpResponse(msg)
        else:
            _logger.warning(
                'Invalid Storage Key in Reading Post: %s', storeKey)
            return HttpResponse('Invalid Key')

    except:
        _logger.exception('Error Storing Reading for ID=%s: %s' %
                          (reading_id, req_data))
        return HttpResponse(sys.exc_info()[1])


# needed to accept HTTP POST requests from systems other than this one.
@csrf_exempt
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
        # if no storeKey, 'bad' will be returned
        storeKey = req_data.get('storeKey', 'bad')
        if store_key_is_valid(storeKey):
            # remove storeKey for security
            del(req_data['storeKey'])
            _logger.debug('Sensor Readings: %s' % req_data)
            msg = storereads.store_many(req_data)
            return HttpResponse(msg)
        else:
            _logger.warning(
                'Invalid Storage Key in Reading Post: %s', storeKey)
            return HttpResponse('Invalid Key')

    except:
        _logger.exception('Error Storing Reading')
        return HttpResponse(sys.exc_info()[1])


# needed to accept HTTP POST requests from systems other than this one.
@csrf_exempt
def store_readings_things(request):
    '''
    Stores a set of sensor readings from the Things Network in the sensor reading
    database. The readings are assumed to originate from an HTTP Integration on an
    Application in the Things Network.  The BMON Store Key is in a custom HTTP header.
    The readings and other data are in the POST data encoded in JSON.
    '''

    try:

        # The post data is JSON, so decode it.
        req_data = json.loads(request.body)

        # See if the store key is valid.  It's stored in the "store-key" header, which
        # is found in the "HTTP_STORE_KEY" key in the META dictionary.
        storeKey = request.META.get('HTTP_STORE_KEY', 'None_Present')

        if store_key_is_valid(storeKey):
            data = decoder.decode(req_data)
            if len(data['fields']) == 0:
                return HttpResponse('No Data Found')

            readings = []
            ts = data['ts']
            eui = data['device_eui']
            # each field is a tuple, normally (field name, value), but it can be
            # (field name, (value, time offset))
            for fld, val in data['fields']:
                if type(val) == tuple:
                    t_offset = val[1]
                    val = val[0]
                else:
                    t_offset = 0.0
                readings.append([ts + t_offset, f'{eui}_{fld}', val])

            msg = storereads.store_many({'readings': readings})
            return HttpResponse(msg)

        else:
            _logger.warning(
                'Invalid Storage Key in Reading Post: %s', storeKey)
            return HttpResponse('Invalid Key')

    except:
        _logger.exception('Error Storing Reading')
        return HttpResponse(sys.exc_info()[1])


# needed to accept HTTP POST requests from systems other than this one.
@csrf_exempt
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
            ts = dateutil.parser.parse(
                req_data['metadata']['time']).timestamp()
            hdw_serial = req_data['hardware_serial']

            pf = req_data['payload_fields']
            event = pf['EVENT_TYPE']
            if event == '01':     # Supervisory Event
                readings.append(
                    [ts, f'{hdw_serial}_battery', float(pf['BATTERY_LEVEL'])])

            elif event == '07':    # Contact event
                val = float(pf['SENSOR_STATE'])
                # Invert their logic: they have a 0 when the contacts are closed
                val = val * -1 + 1
                readings.append([ts, f'{hdw_serial}_state', val])

            elif event == '09':   # Temperature Event
                readings.append(
                    [ts, f'{hdw_serial}_temp', pf['TEMPERATURE'] * 1.8 + 32.])

            else:
                return HttpResponse('No Data')

            msg = storereads.store_many({'readings': readings})

            return HttpResponse(msg)

        else:
            _logger.warning(
                'Invalid Storage Key in Reading Post: %s', storeKey)
            return HttpResponse('Invalid Key')

    except:
        _logger.exception('Error Storing Reading')
        return HttpResponse(sys.exc_info()[1])

# needed to accept HTTP POST requests from systems other than this one.
@csrf_exempt
def store_readings_beaded(request):
    '''
    Stores a set of sensor readings from a BeadedStream Ethernet Activator.
    At the moment, this routine only parses and stored temperature sensors
    connected to the Activator.
    The readings and other data are in the POST data encoded in XML, with
    some extra header and footer lines.
    '''

    try:

        # Check for valid Store Key, which is in the Query parameters.
        storeKey = request.GET.get('storeKey', 'bad')
        if not store_key_is_valid(storeKey):
            _logger.warning(
                'Invalid Storage Key in Reading Post: %s', storeKey)
            return HttpResponse('Invalid Key')

        # make a timestamp for the readings
        ts = time.time()

        # The post data is XML and contains some header and footer lines that need
        # to be stripped.  It returns as a byte string, so decode it into a string.
        data = request.body.decode('utf-8')

        lines = data.splitlines()
        # find start and end of actual XML document.
        for st, lin in enumerate(lines):
            if len(lin) and lin[0] == '<':
                break

        for end in range(len(lines) - 1, 0, -1):
            lin = lines[end]
            if len(lin) and lin[0] == '<':
                break
   
        xml_doc = ''.join(lines[st:end+1])

        root = ET.fromstring(xml_doc)

        # list to hold the possible multiple readings in the XML document.
        readings = []
        for child in root:
            if 'owd_DS18' in child.tag:
                try:
                    for ch2 in child:
                        if 'SensorID' in ch2.tag:
                            sensor_id = 'bs_' + ch2.text
                        elif 'TemperatureCalibrated' in ch2.tag:
                            value = float(ch2.text) * 1.8 + 32.0
                    readings.append( [ts, sensor_id, value])
                except:
                    # problem decoding value
                    _logger.exception('Problem decoding BeadedStream reading.')

        if len(readings) == 0:
            return HttpResponse('No Data Found')

        msg = storereads.store_many({'readings': readings})
        return HttpResponse(msg)

    except:
        _logger.exception('Error Storing Reading')
        return HttpResponse(sys.exc_info()[1])

@csrf_exempt
def store_readings_notehub(request):
    '''
    Stores a set of sensor readings from the Blues Wireless Notehub. The BMON Store Key is
    in a custom HTTP header.
    The readings and other data are in the POST data encoded in JSON.
    '''

    try:

        # The post data is JSON, so decode it.
        req_data = json.loads(request.body)

        # See if the store key is valid.  It's stored in the "store-key" header, which
        # is found in the "HTTP_STORE_KEY" key in the META dictionary.
        storeKey = request.META.get('HTTP_STORE_KEY', 'None_Present')

        if store_key_is_valid(storeKey):

            readings = notehub.extract_readings(req_data)
            msg = storereads.store_many({'readings': readings})
            return HttpResponse(msg)

        else:
            _logger.warning(
                'Invalid Storage Key in Reading Post: %s', storeKey)
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
        _logger.exception('Error Storing Reading for: %s' % req_data)
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
    hide_back_link = True if request.GET.get(
        'hide_back_link') == '1' else False

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
        ret['features'].append({"type": "Feature",
                                "geometry": {"type": "Point",
                                             "coordinates": [bldg.longitude, bldg.latitude]
                                             },
                                "properties": {"facilityName": bldg.title,
                                               "facilityID": bldg.id,
                                               "message": "",
                                               "href": '{}?select_org={}&select_bldg={}'.format(request.build_absolute_uri('../reports/'), org_id, bldg.id)
                                               }
                                })

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
        ctx.update({'success': success, 'access_token': access_token,
                    'refresh_token': refresh_token})
        return render_to_response('bmsapp/ecobee_auth_result.html', ctx)


@login_required(login_url='../admin/login/')
def sensor_data_utilities(request):
    """Utilities for managing sensor data.
    """

    # get the html for the list of buildings and the ID of the a selected building
    # (the first building)
    bldgs_html, bldg_id_selected = view_util.bldg_list_html(0, 0, 0)

    db = bmsdata.BMSdata()
    sensor_list = []
    for sens_id in db.sensor_id_list():
        sensor_info = {'id': sens_id, 'title': ''}
        add_sensor = False

        qs = models.Sensor.objects.filter(sensor_id=sens_id)
        if len(qs) > 0:
            sensor = qs[0]   # get the actual Sensor object
            sensor_info['title'] = sensor.title

            # see if this sensor has links to a building
            links = models.BldgToSensor.objects.filter(sensor=sensor)
            if len(links) > 0:
                # link found
                sensor_info['bldgs'] = [0] + [link['building_id']
                                              for link in links.values()]
                sensor_list.append(sensor_info)

    ctx = base_context()
    ctx.update({'bldgs_html': bldgs_html, 'sensor_list': sensor_list})
    ctx['orgs_hide'] = True
    return render_to_response('bmsapp/sensor-data-utilities.html', ctx)


@login_required(login_url='../admin/login/')
def merge_sensors(request):
    """Merge readings from one sensor to another
    """
    params = request.GET

    action = params.get('action')
    sensor_from = params.get('sensor_from')
    sensor_to = params.get('sensor_to')
    delete_sensor = params.get('delete')

    db = bmsdata.BMSdata()

    try:
        db.cursor.execute(
            f'SELECT min(ts) FROM [{params["sensor_to"]}]')
        where_clause = f' WHERE ts < {db.cursor.fetchone()[0]}'
    except Exception as e:
        return HttpResponse(e, status=500)

    if action == 'query':
        try:
            db.cursor.execute(
                f'SELECT COUNT(*) FROM [{params["sensor_from"]}]' + where_clause)
            rec_ct = db.cursor.fetchone()[0]
        except Exception as e:
            return HttpResponse(e, status=500)
        if rec_ct == 0:
            return HttpResponse(f'No {sensor_from} records found with timestamps earlier than {sensor_to}', status=406)
        else:
            response_text = f'Do you really want to merge {rec_ct:,} records from {sensor_from} into {sensor_to}'
            if delete_sensor == 'on':
                response_text += f' and delete all records from {sensor_from}'
            response_text += '?'
            return HttpResponse(response_text)
    else:
        try:
            db.cursor.execute(
                f'INSERT INTO [{sensor_to}] (ts, val) SELECT ts, val FROM [{sensor_from}]' + where_clause)
            if delete_sensor == 'on':
                db.cursor.execute(f'DROP TABLE [{sensor_from}]')
                qs = models.Sensor.objects.filter(
                    sensor_id=params['sensor_from'])
                if len(qs) > 0:
                    qs[0].delete()
            db.conn.commit()
        except Exception as e:
            return HttpResponse(e, status=500)
        return HttpResponse('Records Merged')


@login_required(login_url='../admin/login/')
def delete_sensor_values(request):
    """Delete values from a sensor
    """
    params = request.GET

    action = params.get('action')
    sensor_id = params.get('sensor')
    delete_where = params.get('delete_where')
    where_value = params.get('value')
    where_start_date = params.get('start_date')
    where_end_date = params.get('end_date')

    db = bmsdata.BMSdata()
    # qs = models.Sensor.objects.filter(sensor_id=params['sensor_from'])[0]

    where_clause = ''

    if delete_where == 'all_values':
        pass
    elif delete_where == 'value_equals':
        where_clause = f'WHERE val = {where_value}'
    elif delete_where == 'values_gt':
        where_clause = f'WHERE val > {where_value}'
    elif delete_where == 'values_lt':
        where_clause = f'WHERE val < {where_value}'
    elif delete_where == 'dates_between':
        where_clause = f'WHERE ts > {bmsapp.data_util.datestr_to_ts(where_start_date)} and ts < {bmsapp.data_util.datestr_to_ts(where_end_date)}'
    else:
        return HttpResponse(f'Invalid parameter: {delete_where}', status=406)

    if action == 'query':
        try:
            db.cursor.execute(
                f'SELECT COUNT(*) FROM [{sensor_id}] {where_clause}')
            rec_ct = db.cursor.fetchone()[0]
        except Exception as e:
            return HttpResponse(e, status=500)
        if rec_ct == 0:
            return HttpResponse('No records found that meet the criteria!', status=406)
        else:
            return HttpResponse(f'Do you really want to delete {rec_ct:,} records from {sensor_id}?')
    else:
        try:
            db.cursor.execute(
                f'DELETE FROM [{sensor_id}] {where_clause}')
            if delete_where == 'all_values':
                db.cursor.execute(f'DROP TABLE [{sensor_id}]')
                qs = models.Sensor.objects.filter(
                    sensor_id=sensor_id)
                if len(qs) > 0:
                    qs[0].delete()
            db.conn.commit()
        except Exception as e:
            return HttpResponse(repr(e), status=500)
        return HttpResponse('Records Deleted')


@login_required(login_url='../admin/login/')
def unassigned_sensors(request):
    """Shows sensors that are in the Reading Database but not assigned to a building.
    """

    db = bmsdata.BMSdata()
    sensor_list = []
    for sens_id in db.sensor_id_list():
        sensor_info = {'id': sens_id, 'title': '',
                       'cur_value': '', 'minutes_ago': ''}
        add_sensor = False

        qs = models.Sensor.objects.filter(sensor_id=sens_id)
        if len(qs) == 0:
            # Sensor does not even have a sensor object
            add_sensor = True
        else:
            sensor = qs[0]   # get the actual Sensor object
            # see if this sensor has links to a building
            links = models.BldgToSensor.objects.filter(sensor=sensor)
            if len(links) == 0:
                # no links, so found an unassigned sensor
                add_sensor = True
                sensor_info['title'] = sensor.title

        if add_sensor:
            last_read = db.last_read(sens_id)
            if last_read:
                val = last_read['val']
                sensor_info['cur_value'] = '%.5g' % val if abs(
                    val) < 1e5 else str(val)
                sensor_info['minutes_ago'] = '%.1f' % (
                    (time.time() - last_read['ts'])/60.0)

            sensor_list.append(sensor_info)

    ctx = base_context()
    ctx.update({'sensor_list': sensor_list})
    return render_to_response('bmsapp/unassigned-sensors.html', ctx)


@login_required(login_url='../admin/login/')
def delete_unassigned_sensor_ids(request):
    """Delete a list of unassigned sensor ids
    """
    try:
        row_ids = request.POST.getlist('row_ids[]')
        db = bmsdata.BMSdata()
        for sensor_id in row_ids:
            db.cursor.execute(f'DROP TABLE [{sensor_id}]')
            qs = models.Sensor.objects.filter(sensor_id=sensor_id)
            if len(qs) > 0:
                qs[0].delete()
        db.conn.commit()
    except Exception as e:
        return HttpResponse(e, status=500)

    return HttpResponse(f'Deleted {len(row_ids)} unassigned sensors')

@login_required(login_url='../admin/login/')
def alert_log(request):
    """Shows a log of alerts that have been issued in the last 60 days.
    """
    
    # timestamp 60 days ago
    ts_min = int(time.time() - 3600 * 24 * 60)

    db = bmsdata.BMSdata()

    db.cursor.execute(f'SELECT * FROM [_alert_log] WHERE ts > {ts_min}')
    alert_list =  [{**x,'when':time.strftime('%Y-%m-%d %H:%M',time.localtime(x['ts']))} for x in [dict(r) for r in db.cursor.fetchall()]]

    ctx = base_context()
    ctx.update({'alert_list': alert_list})
    return render_to_response('bmsapp/alert-log.html', ctx)

@login_required(login_url='../admin/login/')
def backup_reading_db(request):
    """Causes a backup of the sensor reading database to occur.
    """
    bmsapp.scripts.backup_readingdb.run()
    return HttpResponse('Sensor Reading Backup Complete!')

def test_alert_notifications(request):
    """Send test notifications
    """
    try:
        recipient = request.POST.get('recipient')
        recip = models.AlertRecipient.objects.filter(id=recipient)[0]
        result = recip.notify(subject='BMON Test Alert', message='This is a test of a BMON notification that was sent manually by an administrator.', pushover_priority='0')
        if result:
            return HttpResponse(f'The test notifications have been sent.')
        else:
            return HttpResponse(f'Failed to send any notifications!',status=500)
    except Exception as e:
        return HttpResponse(e,status=500)

def test_alert_value(request):
    """Test a value to see if it triggers an alert
    """
    sensor_id = request.POST.get('sensor')
    test_value = request.POST.get('test_value')
    alert = models.AlertCondition.objects.filter(sensor=sensor_id)[0]
    result = alert.check_condition(reading_db=None, override_value=test_value)
    if result:
        subject, msg = result
        return HttpResponse(f'The value triggered an Alert:\n{subject}\n{msg}')
    else:
        return HttpResponse(f'The value did not trigger an Alert')

def wildcard(request, template_name):
    '''
    Used if a URL component doesn't match any of the predefied URL patterns.  Renders
    the template indicated by template_name, adding an '.html' to the name.
    '''
    try:
        template = loader.get_template('bmsapp/%s.html' % template_name)
    except:
        return HttpResponse('Template %s does not exist.' % template_name)
    
    return HttpResponse(template.render(base_context(), request))


@login_required(login_url='../admin/login/')
def password_change_done(request):
    return render_to_response('registration/password_change_done.html',
                              {'user': request.user})
