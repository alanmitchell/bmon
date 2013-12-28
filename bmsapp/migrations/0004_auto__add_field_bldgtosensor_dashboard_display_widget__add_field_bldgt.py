# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'BldgToSensor.dashboard_widget'
        db.add_column(u'bmsapp_bldgtosensor', 'dashboard_widget',
                      self.gf('django.db.models.fields.CharField')(default='NONE', max_length=15),
                      keep_default=False)

        # Adding field 'BldgToSensor.dashboard_row_number'
        db.add_column(u'bmsapp_bldgtosensor', 'dashboard_row_number',
                      self.gf('django.db.models.fields.IntegerField')(default=1),
                      keep_default=False)

        # Adding field 'BldgToSensor.dashboard_column_number'
        db.add_column(u'bmsapp_bldgtosensor', 'dashboard_column_number',
                      self.gf('django.db.models.fields.IntegerField')(default=1),
                      keep_default=False)

        # Adding field 'BldgToSensor.minimum_normal_value'
        db.add_column(u'bmsapp_bldgtosensor', 'minimum_normal_value',
                      self.gf('django.db.models.fields.FloatField')(default=0.0),
                      keep_default=False)

        # Adding field 'BldgToSensor.maximum_normal_value'
        db.add_column(u'bmsapp_bldgtosensor', 'maximum_normal_value',
                      self.gf('django.db.models.fields.FloatField')(default=100.0),
                      keep_default=False)

        # Adding field 'BldgToSensor.minimum_axis_value'
        db.add_column(u'bmsapp_bldgtosensor', 'minimum_axis_value',
                      self.gf('django.db.models.fields.FloatField')(null=True, blank=True),
                      keep_default=False)

        # Adding field 'BldgToSensor.maximum_axis_value'
        db.add_column(u'bmsapp_bldgtosensor', 'maximum_axis_value',
                      self.gf('django.db.models.fields.FloatField')(null=True, blank=True),
                      keep_default=False)

        # Adding field 'BldgToSensor.generate_alert'
        db.add_column(u'bmsapp_bldgtosensor', 'generate_alert',
                      self.gf('django.db.models.fields.BooleanField')(default=False),
                      keep_default=False)

        # Adding field 'BldgToSensor.no_alert_start_date'
        db.add_column(u'bmsapp_bldgtosensor', 'no_alert_start_date',
                      self.gf('django.db.models.fields.DateField')(null=True, blank=True),
                      keep_default=False)

        # Adding field 'BldgToSensor.no_alert_end_date'
        db.add_column(u'bmsapp_bldgtosensor', 'no_alert_end_date',
                      self.gf('django.db.models.fields.DateField')(null=True, blank=True),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'BldgToSensor.dashboard_widget'
        db.delete_column(u'bmsapp_bldgtosensor', 'dashboard_widget')

        # Deleting field 'BldgToSensor.dashboard_row_number'
        db.delete_column(u'bmsapp_bldgtosensor', 'dashboard_row_number')

        # Deleting field 'BldgToSensor.dashboard_column_number'
        db.delete_column(u'bmsapp_bldgtosensor', 'dashboard_column_number')

        # Deleting field 'BldgToSensor.minimum_normal_value'
        db.delete_column(u'bmsapp_bldgtosensor', 'minimum_normal_value')

        # Deleting field 'BldgToSensor.maximum_normal_value'
        db.delete_column(u'bmsapp_bldgtosensor', 'maximum_normal_value')

        # Deleting field 'BldgToSensor.minimum_axis_value'
        db.delete_column(u'bmsapp_bldgtosensor', 'minimum_axis_value')

        # Deleting field 'BldgToSensor.maximum_axis_value'
        db.delete_column(u'bmsapp_bldgtosensor', 'maximum_axis_value')

        # Deleting field 'BldgToSensor.generate_alert'
        db.delete_column(u'bmsapp_bldgtosensor', 'generate_alert')

        # Deleting field 'BldgToSensor.no_alert_start_date'
        db.delete_column(u'bmsapp_bldgtosensor', 'no_alert_start_date')

        # Deleting field 'BldgToSensor.no_alert_end_date'
        db.delete_column(u'bmsapp_bldgtosensor', 'no_alert_end_date')


    models = {
        u'bmsapp.bldgtosensor': {
            'Meta': {'ordering': "('building__title', 'sensor_group__sort_order', 'sort_order')", 'object_name': 'BldgToSensor'},
            'building': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['bmsapp.Building']"}),
            'dashboard_column_number': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'dashboard_row_number': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'dashboard_widget': ('django.db.models.fields.CharField', [], {'default': "'NONE'", 'max_length': '15'}),
            'generate_alert': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'maximum_axis_value': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'maximum_normal_value': ('django.db.models.fields.FloatField', [], {'default': '100.0'}),
            'minimum_axis_value': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'minimum_normal_value': ('django.db.models.fields.FloatField', [], {'default': '0.0'}),
            'no_alert_end_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'no_alert_start_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'sensor': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['bmsapp.Sensor']"}),
            'sensor_group': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['bmsapp.SensorGroup']"}),
            'sort_order': ('django.db.models.fields.IntegerField', [], {'default': '999'})
        },
        u'bmsapp.building': {
            'Meta': {'ordering': "['title']", 'object_name': 'Building'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'latitude': ('django.db.models.fields.FloatField', [], {'default': '62.0'}),
            'longitude': ('django.db.models.fields.FloatField', [], {'default': '-161.0'}),
            'sensors': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': u"orm['bmsapp.Sensor']", 'null': 'True', 'through': u"orm['bmsapp.BldgToSensor']", 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '50'})
        },
        u'bmsapp.chartbuildinginfo': {
            'Meta': {'ordering': "['sort_order']", 'object_name': 'ChartBuildingInfo'},
            'building': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['bmsapp.Building']"}),
            'chart': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['bmsapp.MultiBuildingChart']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'parameters': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'sort_order': ('django.db.models.fields.IntegerField', [], {'default': '999'})
        },
        u'bmsapp.multibuildingchart': {
            'Meta': {'ordering': "['sort_order']", 'object_name': 'MultiBuildingChart'},
            'chart_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['bmsapp.MultiBuildingChartType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'parameters': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'sort_order': ('django.db.models.fields.IntegerField', [], {'default': '999'}),
            'title': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '60'})
        },
        u'bmsapp.multibuildingcharttype': {
            'Meta': {'ordering': "['sort_order']", 'object_name': 'MultiBuildingChartType'},
            'class_name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'sort_order': ('django.db.models.fields.IntegerField', [], {'default': '999'}),
            'title': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '50'})
        },
        u'bmsapp.sensor': {
            'Meta': {'ordering': "['sensor_id']", 'object_name': 'Sensor'},
            'calculation_order': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'function_parameters': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_calculated': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'sensor_id': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '15'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'tran_calc_function': ('django.db.models.fields.CharField', [], {'max_length': '35', 'blank': 'True'}),
            'unit': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['bmsapp.Unit']"})
        },
        u'bmsapp.sensorgroup': {
            'Meta': {'ordering': "['sort_order']", 'object_name': 'SensorGroup'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'sort_order': ('django.db.models.fields.IntegerField', [], {'default': '999'}),
            'title': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '40'})
        },
        u'bmsapp.unit': {
            'Meta': {'ordering': "['measure_type', 'label']", 'object_name': 'Unit'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'label': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '20'}),
            'measure_type': ('django.db.models.fields.CharField', [], {'max_length': '30'})
        }
    }

    complete_apps = ['bmsapp']