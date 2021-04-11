'''
This file configures the Admin interface, which allows for editing of the Models.
'''

from bmsapp.models import Building, Sensor, SensorGroup, BldgToSensor, DashboardItem, Unit
from bmsapp.models import MultiBuildingChart, ChartBuildingInfo, CustomReport
from bmsapp.models import Organization, BuildingGroup, BuildingMode
from bmsapp.models import AlertCondition, AlertRecipient, PeriodicScript
from bmsapp.models import FuelRate, ElectricRate
from django.contrib import admin
from django.forms import TextInput, Textarea
from django.db import models
from django.utils.html import format_html
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _


class BldgToSensorInline(admin.TabularInline):
    '''Used in Building change form.
    '''
    model = BldgToSensor
    extra = 1
    fields = ('sensor', 'edit_sensor', 'sensor_group', 'sort_order')

    def edit_sensor(self, instance):
        url = reverse('admin:bmsapp_sensor_change', args=(instance.sensor.pk,))
        return format_html('<a href="{}">Edit this Sensor</a>', url)

    readonly_fields = ('edit_sensor',)


class BldgToSensorInline2(admin.TabularInline):
    '''Used in Sensor change form.
    '''
    model = BldgToSensor
    extra = 1


class DashboardItemInline(admin.StackedInline):
    model = DashboardItem
    extra = 1

    fieldsets = (
        (None, {'fields': ( ('widget_type', 'row_number', 'column_number'),
                            ('sensor', 'title'),
                            ('minimum_normal_value', 'maximum_normal_value', 'minimum_axis_value', 'maximum_axis_value'),
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


@admin.register(Building)
class BuildingAdmin(admin.ModelAdmin):
    inlines = (BldgToSensorInline, DashboardItemInline)
    formfield_overrides = {
        models.TextField: {'widget': Textarea(attrs={'rows': 6, 'cols':80})},
    }
    def get_form(self, request, obj=None, **kwargs):
        # save the object reference for future processing in DashboardInline
        request._obj_ = obj
        return super(BuildingAdmin, self).get_form(request, obj, **kwargs)


@admin.register(BuildingMode)
class BuildingModeAdmin(admin.ModelAdmin):
    list_display = ('name',)
    list_editable = ('name',)
    list_display_links = None


@admin.register(BuildingGroup)
class BuildingGroupAdmin(admin.ModelAdmin):
    filter_horizontal = ('buildings',)

@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    filter_horizontal = ('buildings', 'building_groups', 'multi_charts', 'custom_reports')

class AlertAdminInline(admin.StackedInline):
    '''Used in the Sensor Admin to enter alerts.
    '''
    model = AlertCondition
    template = "admin/stacked_alerts.html"
    extra = 0
    filter_horizontal = ('recipients',)

    fieldsets = (
        (None, {'fields': ( ('active', 'sensor'),
                            ('condition', 'test_value', 'read_count'),
                            ('only_if_bldg', 'only_if_bldg_mode','only_if_bldg_status'),
                            ('alert_message',),
                            ('priority', 'wait_before_next'),
                            ('recipients',)
                          )}
        ),
    )

    formfield_overrides = {
        models.TextField: {'widget': Textarea(attrs={'rows':3, 'cols':80})},
    }


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

class SensorAlertExistsListFilter(admin.SimpleListFilter):
    '''List Filter used to select sensors that have alerts present.
    See https://docs.djangoproject.com/en/2.2/ref/contrib/admin/#django.contrib.admin.ModelAdmin.list_filter
    for info on how this built.
    '''

    # Human-readable title which will be displayed in the
    # right admin sidebar just above the filter options.
    # NOTE:  the underbar is a function imported from django.utils.translation
    title = _('Alerts Present')

    # Parameter for the filter that will be used in the URL query.
    parameter_name = 'alerts_present'

    def lookups(self, request, model_admin):
        """
        Returns a list of tuples. The first element in each
        tuple is the coded value for the option that will
        appear in the URL query. The second element is the
        human-readable name for the option that will appear
        in the right sidebar.
        """
        return (
            ('active', _('Have Active Alerts')),
            ('inactive', _('Have Inactive Alerts')),
            ('none', _('Have No Alerts')),
        )

    def queryset(self, request, queryset):
        """
        Returns the filtered queryset based on the value
        provided in the query string and retrievable via
        `self.value()`.
        """
        # get the requested alert presence.
        alert_presence = self.value()
        if alert_presence is None:
            # This case occurs when 'All' is selected
            return queryset
        elif alert_presence == 'none':
            sensor_ids = [alert.sensor.pk for alert in AlertCondition.objects.all()]
            sensor_ids = list(set(sensor_ids))
            return queryset.exclude(pk__in=sensor_ids)
        elif alert_presence == 'inactive':
            sensor_ids = [alert.sensor.pk for alert in AlertCondition.objects.filter(active=False)]
            sensor_ids = list(set(sensor_ids))
            return queryset.filter(pk__in=sensor_ids)
        elif alert_presence == 'active':
            sensor_ids = [alert.sensor.pk for alert in AlertCondition.objects.filter(active=True)]
            sensor_ids = list(set(sensor_ids))
            return queryset.filter(pk__in=sensor_ids)
        else:
            return queryset

@admin.register(Sensor)
class SensorAdmin(admin.ModelAdmin):
    inlines = (BldgToSensorInline2, AlertAdminInline)
    search_fields = ['sensor_id', 'title', 'tran_calc_function']
    list_filter = [BuildingSensorListFilter, SensorAlertExistsListFilter, 'is_calculated']
    formfield_overrides = {
        models.TextField: {'widget': Textarea(attrs={'rows':6, 'cols':80})},
    }


@admin.register(SensorGroup)
class SensorGroupAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'sort_order')
    list_editable = ('title', 'sort_order')


@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    list_display = ('id', 'label', 'measure_type')
    list_editable = ('label', 'measure_type')


class ChartBuildingInfoInline(admin.TabularInline):
    model = ChartBuildingInfo
    formfield_overrides = {
        models.TextField: {'widget': Textarea(attrs={'rows':5, 'cols':40})},
    }
    extra = 1


@admin.register(MultiBuildingChart)
class MultiBuildingChartAdmin(admin.ModelAdmin):
    inlines = (ChartBuildingInfoInline,)
    formfield_overrides = {
        models.TextField: {'widget': Textarea(attrs={'rows':6, 'cols':40})},
    }

@admin.register(AlertRecipient)
class AlertRecipientAdmin(admin.ModelAdmin):
    change_form_template = 'admin/AlertRecipient_change_form.html'
    list_display = ('name', 'active' )
    list_editable= ('active',)
    fields = (
        ('active', 'name'), 
        ('notify_email', 'email_address'), 
        ('notify_cell', 'cell_number', 'cell_sms_gateway'),
        ('notify_pushover', 'pushover_id')
    )

@admin.register(PeriodicScript)
class SensorAdmin(admin.ModelAdmin):
    exclude = ('hidden_script_results', )
    list_display =  ('script_file_name', 'description', 'period', 'script_parameters')
    search_fields = ['script_file_name', 'description', 'script_parameters']
    readonly_fields = ('script_results',)
    formfield_overrides = {
        models.TextField: {'widget': Textarea(attrs={'rows': 8, 'cols': 80})},
    }

@admin.register(CustomReport)
class CustomReportAdmin(admin.ModelAdmin):
    list_display = ('title', 'group')
    formfield_overrides = {models.TextField: {'widget': Textarea(attrs={'rows':20, 'cols':80})}}

@admin.register(FuelRate)
class FuelRateAdmin(admin.ModelAdmin):
    list_display = ('title',)

@admin.register(ElectricRate)
class ElectricRateAdmin(admin.ModelAdmin):
    list_display = ('title',)
