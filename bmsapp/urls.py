'''
URLs for the BMS Application
'''

from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^readingdb/reading/(\w+)/store/$', views.store_reading),      # URL to store one reading into database
    url(r'^readingdb/reading/store/$', views.store_readings),          # URL to store multiple readings into database
    url(r'^st8(\w+)/', views.store_reading_old),             # Old URL pattern for storing.  Shouldn't be used for new sensors.
    url(r'^readingdb/reading/(\w+)/$', views.get_readings),   # gets all readings for one reading ID.
    url(r'^$', views.index, name='index'),
    url(r'^reports/$', views.reports, name='reports'),
    url(r'^reports/results/$', views.get_report_results),
    url(r'^reports/embed/$', views.get_embedded_results), # javascript embedded version of report results
    url(r'^reports/(\d+)/$', views.reports),
    url(r'^custom-reports/$', views.custom_report_list),
    url(r'^custom-reports/(.+)$', views.custom_report),
    url(r'^show-log/$', views.show_log),
    url(r'^bldg-list/(\d+)/$', views.bldg_list),
    url(r'^chart-sensor-list/(\d+)/(multi)/$', views.chart_sensor_list),
    url(r'^chart-sensor-list/(\d+)/(\d+)/$', views.chart_sensor_list),
    url(r'^map-json/$', views.map_json, name='map-json'),
    url(r'^training/video/(\w+)/(\d+)/(\d+)/$', views.show_video, name='show-video'),
    url(r'^make-store-key/$', views.make_store_key),
    url(r'^ecobee-auth/$', views.ecobee_auth),

    # catches URLs that don't match the above patterns.  Assumes they give a template name to render.
    url(r'^([^.]+)/$', views.wildcard, name='wildcard'),
]
