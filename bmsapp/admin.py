'''
This file configures the Admin interface, which allows for editing of the Models.
'''

from bmsapp.models import Building, Sensor, SensorGroup, BldgToSensor, DashboardItem, Unit
from bmsapp.models import MultiBuildingChart, ChartBuildingInfo
from bmsapp.models import BuildingGroup
from django.contrib import admin
from django.forms import TextInput, Textarea
from django.db import models
from django.utils.translation import ugettext_lazy as _


class BldgToSensorInline(admin.TabularInline):
    model = BldgToSensor
    extra = 1


class DashboardItemInline(admin.StackedInline):
    model = DashboardItem
    extra = 1

    fieldsets = (
        (None, {'fields': ( ('widget_type', 'row_number', 'column_number'),
                            ('sensor', 'title'),
                            ('minimum_normal_value', 'maximum_normal_value', 'minimum_axis_value', 'maximum_axis_value'),
                            ('generate_alert', 'no_alert_start_date', 'no_alert_end_date'),
                          )}
        ),
    )
    formfield_overrides = {
        models.FloatField: {'widget': TextInput(attrs={'size':'10'})},
        models.IntegerField: {'widget': TextInput(attrs={'size':'5'})},
    }
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        # Filter sensor list down to just those for this building.
        if db_field.name == "sensor":
            kwargs["queryset"] = BldgToSensor.objects.filter(building__exact = request._obj_)
        return super(DashboardItemInline, self).formfield_for_foreignkey(db_field, request, **kwargs)


class BuildingAdmin(admin.ModelAdmin):
    inlines = (BldgToSensorInline, DashboardItemInline)
    formfield_overrides = {
        models.TextField: {'widget': Textarea(attrs={'rows': 4})},
    }
    def get_form(self, request, obj=None, **kwargs):
        # save the object reference for future processing in DashboardInline
        request._obj_ = obj
        return super(BuildingAdmin, self).get_form(request, obj, **kwargs)


class BuildingGroupAdmin(admin.ModelAdmin):
    filter_horizontal = ('buildings',)


class BuildingSensorListFilter(admin.SimpleListFilter):
    '''List Filter used to select sensors belonging to a
    particular building when on the Sensor Admin page (below).
    See https://docs.djangoproject.com/en/1.7/ref/contrib/admin/#django.contrib.admin.ModelAdmin.list_filter
    for info on how this built.
    '''

    # Human-readable title which will be displayed in the
    # right admin sidebar just above the filter options.
    # NOTE:  the underbar is a function imported from django.utils.translation
    title = _('Building')

    # Parameter for the filter that will be used in the URL query.
    parameter_name = 'bldg_id'

    def lookups(self, request, model_admin):
        """
        Returns a list of tuples. The first element in each
        tuple is the coded value for the option that will
        appear in the URL query. The second element is the
        human-readable name for the option that will appear
        in the right sidebar.
        """
        return [(str(b.pk), _(b.title)) for b in Building.objects.all()]

    def queryset(self, request, queryset):
        """
        Returns the filtered queryset based on the value
        provided in the query string and retrievable via
        `self.value()`.
        """
        # get the ID of the requested building and find the sensor IDs
        # associated with that building.
        bldg_pk = self.value()
        if bldg_pk is None:
            # This case occurs when 'All' buildings are selected
            return queryset
        else:
            sensor_ids = [b_to_s.sensor.pk for b_to_s in BldgToSensor.objects.filter(building_id=bldg_pk)]
            return queryset.filter(pk__in=sensor_ids)


class SensorAdmin(admin.ModelAdmin):
    inlines = (BldgToSensorInline,)
    search_fields = ['sensor_id', 'title', 'tran_calc_function']
    list_filter = ['is_calculated', BuildingSensorListFilter]


class SensorGroupAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'sort_order')
    list_editable = ('title', 'sort_order')


class UnitAdmin(admin.ModelAdmin):
    list_display = ('id', 'label', 'measure_type')
    list_editable = ('label', 'measure_type')


class ChartBuildingInfoInline(admin.TabularInline):
    model = ChartBuildingInfo
    formfield_overrides = {
        models.TextField: {'widget': Textarea(attrs={'rows':5, 'cols':40})},
    }
    extra = 1


class MultiBuildingChartAdmin(admin.ModelAdmin):
    inlines = (ChartBuildingInfoInline,)
    formfield_overrides = {
        models.TextField: {'widget': Textarea(attrs={'rows':6, 'cols':40})},
    }


admin.site.register(Building, BuildingAdmin)
admin.site.register(BuildingGroup, BuildingGroupAdmin)
admin.site.register(Sensor, SensorAdmin)
admin.site.register(SensorGroup, SensorGroupAdmin)
admin.site.register(Unit, UnitAdmin)
admin.site.register(MultiBuildingChart, MultiBuildingChartAdmin)
