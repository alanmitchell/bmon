from django.urls import include, path

# Uncomment the next two lines to enable the admin:
from django.contrib import admin

urlpatterns = [
    # Uncomment the admin/doc line below to enable admin documentation:
    path(r'admin/doc/', include('django.contrib.admindocs.urls')),
    path(r'admin/', admin.site.urls),
    path(r'', include('bmsapp.urls')),
]

admin.site.site_title = 'BMON Admin'
admin.site.site_header = 'BMON Administration'
admin.site.index_title = 'Site Administration'
