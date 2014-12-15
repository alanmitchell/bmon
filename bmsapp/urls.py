'''
URLs for the BMS Application
'''

from django.conf.urls import patterns, url

urlpatterns = patterns('bmsapp.views',
    url(r'^readingdb/reading/(\w+)/store/$', 'store_reading'),      # URL to store one reading into database
    url(r'^readingdb/reading/store/$', 'store_readings'),          # URL to store multiple readings into database
    url(r'^st8(\w+)/', 'store_reading_old'),             # Old URL pattern for storing.  Shouldn't be used for new sensors.
    url(r'^readingdb/reading/(\w+)/$', 'get_readings'),   # gets all readings for one reading ID.
    url(r'^$', 'index'),
    url(r'^reports/$', 'reports', name='reports'),
    url(r'^reports/(\d+)/$', 'reports'),
    url(r'^show_log/$', 'show_log'),
    url(r'^bldg_list/(\d+)/$', 'bldg_list'),
    url(r'^chart_sensor_list/(\d+)/(multi)/$', 'chart_sensor_list'),
    url(r'^chart_sensor_list/(\d+)/(\d+)/$', 'chart_sensor_list'),
    url(r'^chart/(multi|\d+)/(\d+)/([a-zA-Z_]+)/', 'chart_info'),
    url(r'^map_json/$', 'map_json', name='map-json'),
    url(r'^training/video/(\w+)/(\d+)/(\d+)/$', 'show_video', name='show-video'),
    url(r'^make_store_key/$', 'make_store_key'),

    # catches URLs that don't match the above patterns.  Assumes they give a template name to render.
    url(r'^(\w+)/$', 'wildcard'),      
)
