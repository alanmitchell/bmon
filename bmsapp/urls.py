﻿'''
URLs for the BMS Application
'''

from django.conf.urls import url
from django.urls import re_path
from . import views
from . import views_api_v1

# Could work on simplifying many of these by usin the new "path" function
urlpatterns = [
    re_path(r'^readingdb/reading/(\w+)/store/$', views.store_reading),      # URL to store one reading into database
    re_path(r'^readingdb/reading/store/$', views.store_readings),          # URL to store multiple readings into database
    re_path(r'^st8(\w+)/', views.store_reading_old),             # Old URL pattern for storing.  Shouldn't be used for new sensors.
    re_path(r'^readingdb/reading/(\w+)/$', views.get_readings),   # gets all readings for one reading ID.
    re_path(r'^$', views.index, name='index'),
    re_path(r'^reports/$', views.reports, name='reports'),
    re_path(r'^reports/results/$', views.get_report_results),
    re_path(r'^reports/embed/$', views.get_embedded_results), # javascript embedded version of report results
    re_path(r'^custom-reports/$', views.custom_report_list),
    re_path(r'^custom-reports/(.+)$', views.custom_report),
    re_path(r'^show-log/$', views.show_log),
    re_path(r'^group-list/(\d+)/$', views.group_list),
    re_path(r'^bldg-list/(\d+)/(\d+)/$', views.bldg_list),
    re_path(r'^chart-sensor-list/(\d+)/(multi)/$', views.chart_sensor_list),
    re_path(r'^chart-sensor-list/(\d+)/(\d+)/$', views.chart_sensor_list),
    re_path(r'^map-json/$', views.map_json, name='map-json'),
    re_path(r'^training/video/(\w+)/(\d+)/(\d+)/$', views.show_video, name='show-video'),
    re_path(r'^make-store-key/$', views.make_store_key),
    re_path(r'^ecobee-auth/$', views.ecobee_auth),
    re_path(r'^unassigned-sensors/$', views.unassigned_sensors),
    re_path(r'^backup-readings/$', views.backup_reading_db),

    # Views related to the API, version 1
    re_path(r'^api/v1/readings/(.+)/$', views_api_v1.sensor_readings),
    re_path(r'^api/v1/sensors/$', views_api_v1.sensor_list),

    # catches URLs that don't match the above patterns.  Assumes they give a template name to render.
    re_path(r'^([^.]+)/$', views.wildcard, name='wildcard'),
]
