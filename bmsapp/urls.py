'''
URLs for the BMS Application
'''

from django.conf.urls import patterns, url

urlpatterns = patterns('bmsapp.views',
    url(r'^readingdb/reading/(\w+)/store/', 'store_reading'),          # URL to store readings into database
    url(r'^st8(\w+)/', 'store_reading_old'),             # Old URL pattern for storing.  Shouldn't be used for new sensors.
    url(r'^$', 'index'),
    url(r'^reports/$', 'reports', name='reports'),
    url(r'^reports/(multi|\d+)/$', 'reports'),
    url(r'^reports/(multi|\d+)/(\d+)/$', 'reports'),
    url(r'^reports/(multi|\d+)/(\d+)/(\w+)/$', 'reports', name='reports-bldg-chart-sensor'),
    url(r'^show_log/$', 'show_log'),
    url(r'^chart_list/(multi)/$', 'chart_list'),
    url(r'^chart_list/(\d+)/$', 'chart_list'),
    url(r'^chart/(multi|\d+)/(\d+)/([a-zA-Z_]+)/', 'chart_info'),
    url(r'^map_json/$', 'map_json', name='map-json'),
    url(r'^training/video/(\w+)/(\d+)/(\d+)/$', 'show_video', name='show-video'),
    url(r'^make_store_key/$', 'make_store_key'),

    # catches URLs that don't match the above patterns.  Assumes they give a template name to render.
    url(r'^(\w+)/$', 'wildcard'),      
)
