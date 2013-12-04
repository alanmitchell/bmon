'''
This file configures the Admin interface, which allows for editing of the Models.
'''

from bmsapp.models import Building, Sensor, SensorGroup, BldgToSensor, Unit
from bmsapp.models import MultiBuildingChartType, MultiBuildingChart, ChartBuildingInfo
from django.contrib import admin
from django.forms import TextInput, Textarea
from django.db import models

class BldgToSensorInline(admin.TabularInline):
    model = BldgToSensor
    extra = 1

class BuildingAdmin(admin.ModelAdmin):
    inlines = (BldgToSensorInline, )

class SensorAdmin(admin.ModelAdmin):
    inlines = (BldgToSensorInline,)
    search_fields = ['title', 'tran_calc_function']
    list_filter = ['is_calculated', 'tran_calc_function']

class SensorGroupAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'sort_order')
    list_editable = ('title', 'sort_order')

class UnitAdmin(admin.ModelAdmin):
    list_display = ('id', 'label', 'measure_type')
    list_editable = ('label', 'measure_type')

class MultiBuildingChartTypeAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'class_name', 'sort_order')
    list_editable = ('title', 'class_name', 'sort_order')

class ChartBuildingInfoInline(admin.TabularInline):
    model = ChartBuildingInfo
    formfield_overrides = {
        models.TextField: {'widget': Textarea(attrs={'rows':1, 'cols':60})},
    }
    extra = 1

class MultiBuildingChartAdmin(admin.ModelAdmin):
    inlines = (ChartBuildingInfoInline,)
    formfield_overrides = {
        models.TextField: {'widget': Textarea(attrs={'rows':1, 'cols':60})},
    }

admin.site.register(Building, BuildingAdmin)
admin.site.register(Sensor, SensorAdmin)
admin.site.register(SensorGroup, SensorGroupAdmin)
admin.site.register(Unit, UnitAdmin)
admin.site.register(MultiBuildingChartType, MultiBuildingChartTypeAdmin)
admin.site.register(MultiBuildingChart, MultiBuildingChartAdmin)
