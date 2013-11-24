# Create your views here.
from  django.http import HttpResponse
from django.shortcuts import render_to_response, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.core.urlresolvers import reverse
import models, storereads, global_vars, charts, view_util
import sys, logging, json

# Make a logger for this module
_logger = logging.getLogger('bms.' + __name__)

def index(request):
    '''
    The main home page for the site, which redirects to the desired page to show for the home page.
    '''
    #return redirect('/map/')
    return redirect( reverse('bmsapp.views.map') )

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
    chart = view_util.chart_from_id(bldg_id_selected, chart_id_selected)
    chart_class = getattr(charts, chart.chart_type.class_name)     # get the class name to instantiate a chart object
    chart_obj = chart_class(chart, request.GET)                    # Make the chart object from the class
    chart_html = chart_obj.html(selected_sensor)

    return render_to_response('bmsapp/reports.html', {'bldgs_html': bldgs_html, 'chart_list_html': chart_list_html, 'chart_html': chart_html})

def show_log(request):
    '''
    Returns the application's log file, without formatting.
    '''
    return HttpResponse('<pre>%s</pre>' % open(global_vars.LOG_FILE).read())

@csrf_exempt    # needed to accept HTTP POST requests from the AHFC BAS system.
def store_reading(request):
    '''
    Stores a sensor reading in the sensor reading database.  The sensor reading information is
    provided in the GET parameters of the request.
    '''
    try:
        # determine whether request was a GET or POST and extract data
        data = request.GET.dict() if request.method == 'GET' else request.POST.dict()

        # get the Sensor object, if available, to pass along a transform function
        sensors = models.Sensor.objects.filter( sensor_id=data['id'] )
        if len(sensors)>0:
            # Take first sensor in list ( should be only one )
            storereads.store(data, sensors[0].tran_calc_function, sensors[0].function_parameters)
        else:
            # no sensor with the requested ID was found.  Therefore, no transform function and parameters
            # to pass.
            storereads.store(data)

        return HttpResponse('OK')

    except:
        _logger.exception('Error Storing Reading: %s' % request.GET.dict())
        return HttpResponse('Error Storing: %s' % request.GET.dict())

def store_test(request):
    _logger.info('store_test GET Parameters: %s' % request.GET.dict())
    return HttpResponse('%s' % request.GET.dict())


def chart_list(request, selected_bldg):
    '''
    Returns a JSON array of the charts that are available for the building with the pk ID
    of 'bldg'.  If 'bldg' is the string 'multi', the list of multi-building charts is returned.
    The return value is an array of objects, each object having an 'id' property, giving the pk ID
    of the chart, and a 'title' property giving the title of the chart.
    '''

    # try to convert the selected building value to an integer (might be the string 'multi') so that
    # it will match the integer IDs in the database.
    selected_bldg = view_util.to_int(selected_bldg)

    charts_html, id_selected = view_util.chart_list_html(selected_bldg)

    return HttpResponse(charts_html)


def chart_info(request, bldg_group, chart_id, info_type):
    '''
    Returns the HTML or data needed to display a chart
    'bldg_group' is either 'one' or 'multi', indicating whether the chart is for one 
    building (one) or a group of buildings (multi). 'chart_id' is the pk ID of the chart requested.
    'info_type' is the type of chart information requested: 'html' to request the HTML for
    the chart page, 'data' to request the data for the chart, or the name of a method on the 
    created chart class to call to return data.
    '''

    try:
        # get the chart object from the model
        chart = view_util.chart_from_id(bldg_group, chart_id)

        # get the appropriate class to instantiate a chart object
        chart_class = getattr(charts, chart.chart_type.class_name)

        # Make the chart object from the class
        chart_obj = chart_class(chart, request.GET)

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

def map(request):
    '''
    The map page.
    '''
    return render_to_response('bmsapp/map.html', {}) 


def training(request):
    '''
    The training page.
    '''

    return render_to_response('bmsapp/training.html', {})   #, {'building_list': bldgs})

def show_video(request, filename, width, height):
    '''
    A Page to show a training video.  'filename' is the Flash file name of the video, without
    the 'swf' extension, 'width' and 'height' are the width and height in pixels of the viewport.
    '''

    return render_to_response('bmsapp/video.html', {'filename': filename, 'width': width, 'height': height}) 


@login_required
def password_change_done(request):
    return render_to_response('registration/password_change_done.html',
        {'user': request.user})

