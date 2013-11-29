'''
URLs for the BMS Application
'''

from django.conf.urls import patterns, url

urlpatterns = patterns('bmsapp.views',
    url(r'^$', 'index'),
    url(r'^reports/$', 'reports', name='reports'),
    url(r'^reports/(multi|\d+)/$', 'reports'),
    url(r'^reports/(multi|\d+)/(\d+)/$', 'reports'),
    url(r'^reports/(multi|\d+)/(\d+)/(\w+)/$', 'reports', name='reports-bldg-chart-sensor'),
    url(r'^stB3D82/', 'store_reading'),                    # toy security: obscure the URL
    url(r'^store_test/$', 'store_test'),
    url(r'^show_log/$', 'show_log'),
    url(r'/chart_list/(multi)/$', 'chart_list'),
    url(r'/chart_list/(\d+)/$', 'chart_list'),
    url(r'/chart/(multi|one)/(\d+)/([a-zA-Z_]+)/', 'chart_info'),
    url(r'^training/video/(\w+)/(\d+)/(\d+)/$', 'show_video', name='show-video'),

    # catches URLs that don't match the above patterns.  Assumes they give a template name to render.
    url(r'^(\w+)/$', 'wildcard'),      
)
