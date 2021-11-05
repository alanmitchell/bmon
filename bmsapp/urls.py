'''
URLs for the BMS Application
'''

from django.conf.urls import url
from django.urls import re_path
from bmsapp import views
from bmsapp import views_api_v1
from bmsapp import views_api_v2

# Could work on simplifying many of these by using the new "path" function
urlpatterns = [
    # URL to store one reading into database
    re_path(r'^readingdb/reading/(\w+)/store/$', views.store_reading),
    # URL to store multiple readings into database
    re_path(r'^readingdb/reading/store/$', views.store_readings),
    # URL to store readings from Things Network
    re_path(r'^readingdb/reading/store-things/$', views.store_readings_things),
    re_path(r'^readingdb/reading/store-rb/$',
            views.store_readings_radio_bridge),
    re_path(r'^readingdb/reading/store-beaded/$', views.store_readings_beaded),
    re_path(r'^readingdb/reading/store-notehub/$', views.store_readings_notehub),
    # Old URL pattern for storing.  Shouldn't be used for new sensors.
    re_path(r'^st8(\w+)/', views.store_reading_old),
    # gets all readings for one reading ID.
    re_path(r'^readingdb/reading/(\w+)/$', views.get_readings),
    re_path(r'^$', views.index, name='index'),
    re_path(r'^reports/$', views.reports, name='reports'),
    re_path(r'^reports/results/$', views.get_report_results),
    # javascript embedded version of report results
    re_path(r'^reports/embed/$', views.get_embedded_results),
    re_path(r'^energy-reports/$', views.energy_reports),
    re_path(r'^custom-reports/$', views.custom_report_list),
    re_path(r'^custom-reports/(.+)$', views.custom_report),
    re_path(r'^show-log/$', views.show_log),
    re_path(r'^group-list/(\d+)/$', views.group_list),
    re_path(r'^bldg-list/(\d+)/(\d+)/$', views.bldg_list),
    re_path(r'^chart-sensor-list/(\d+)/(multi)/$', views.chart_sensor_list),
    re_path(r'^chart-sensor-list/(\d+)/(\d+)/$', views.chart_sensor_list),
    re_path(r'^map-json/$', views.map_json, name='map-json'),
    re_path(r'^training/video/(\w+)/(\d+)/(\d+)/$',
            views.show_video, name='show-video'),
    re_path(r'^make-store-key/$', views.make_store_key),
    re_path(r'^ecobee-auth/$', views.ecobee_auth),
    
    re_path(r'^unassigned-sensors/$', views.unassigned_sensors),
    re_path(r'^unassigned-sensors/delete_ids/$',
            views.delete_unassigned_sensor_ids),
    re_path(r'^backup-readings/$', views.backup_reading_db),
    re_path(r'^sensor-data-utilities/$', views.sensor_data_utilities),
    re_path(r'^merge-sensors/$', views.merge_sensors),
    re_path(r'^delete-sensor-values/$', views.delete_sensor_values),

    re_path(r'^test-alert-notifications/$', views.test_alert_notifications),
    re_path(r'^test-alert-value/$', views.test_alert_value),
    re_path(r'^alert-log/$', views.alert_log),

    # Views related to the API, version 1
    re_path(r'^api/v1/version/$', views_api_v1.api_version),
    re_path(r'^api/v1/readings/(.+)/$', views_api_v1.sensor_readings),
    re_path(r'^api/v1/sensors/$', views_api_v1.sensor_list),

    # Views related to the API, version 2
    re_path(r'^api/v2/version/$', views_api_v2.api_version),
    re_path(r'^api/v2/readings/$', views_api_v2.sensor_readings),
    re_path(r'^api/v2/sensors/$', views_api_v2.sensors),
    re_path(r'^api/v2/buildings/$', views_api_v2.buildings),
    re_path(r'^api/v2/organizations/$', views_api_v2.organizations),

    # catches URLs that don't match the above patterns.  Assumes they give a template name to render.
    re_path(r'^([^.]+)/$', views.wildcard, name='wildcard'),
]
