# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'SensorGroup'
        db.create_table(u'bmsapp_sensorgroup', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('title', self.gf('django.db.models.fields.CharField')(unique=True, max_length=40)),
            ('sort_order', self.gf('django.db.models.fields.IntegerField')(default=999)),
        ))
        db.send_create_signal(u'bmsapp', ['SensorGroup'])

        # Adding model 'Unit'
        db.create_table(u'bmsapp_unit', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('label', self.gf('django.db.models.fields.CharField')(unique=True, max_length=20)),
            ('measure_type', self.gf('django.db.models.fields.CharField')(max_length=30)),
        ))
        db.send_create_signal(u'bmsapp', ['Unit'])

        # Adding model 'Sensor'
        db.create_table(u'bmsapp_sensor', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('sensor_id', self.gf('django.db.models.fields.CharField')(unique=True, max_length=15)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('unit', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['bmsapp.Unit'])),
            ('is_calculated', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('tran_calc_function', self.gf('django.db.models.fields.CharField')(max_length=35, blank=True)),
            ('function_parameters', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('calculation_order', self.gf('django.db.models.fields.IntegerField')(default=0)),
        ))
        db.send_create_signal(u'bmsapp', ['Sensor'])

        # Adding model 'BuildingChartType'
        db.create_table(u'bmsapp_buildingcharttype', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('title', self.gf('django.db.models.fields.CharField')(unique=True, max_length=50)),
            ('class_name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=30)),
            ('sort_order', self.gf('django.db.models.fields.IntegerField')(default=999)),
        ))
        db.send_create_signal(u'bmsapp', ['BuildingChartType'])

        # Adding model 'MultiBuildingChartType'
        db.create_table(u'bmsapp_multibuildingcharttype', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('title', self.gf('django.db.models.fields.CharField')(unique=True, max_length=50)),
            ('class_name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=30)),
            ('sort_order', self.gf('django.db.models.fields.IntegerField')(default=999)),
        ))
        db.send_create_signal(u'bmsapp', ['MultiBuildingChartType'])

        # Adding model 'Building'
        db.create_table(u'bmsapp_building', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('title', self.gf('django.db.models.fields.CharField')(unique=True, max_length=50)),
        ))
        db.send_create_signal(u'bmsapp', ['Building'])

        # Adding model 'BldgToSensor'
        db.create_table(u'bmsapp_bldgtosensor', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('building', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['bmsapp.Building'])),
            ('sensor', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['bmsapp.Sensor'])),
            ('sensor_group', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['bmsapp.SensorGroup'])),
            ('sort_order', self.gf('django.db.models.fields.IntegerField')(default=999)),
        ))
        db.send_create_signal(u'bmsapp', ['BldgToSensor'])

        # Adding model 'BuildingChart'
        db.create_table(u'bmsapp_buildingchart', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('building', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['bmsapp.Building'])),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=60)),
            ('chart_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['bmsapp.BuildingChartType'])),
            ('parameters', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('sort_order', self.gf('django.db.models.fields.IntegerField')(default=999)),
        ))
        db.send_create_signal(u'bmsapp', ['BuildingChart'])

        # Adding model 'MultiBuildingChart'
        db.create_table(u'bmsapp_multibuildingchart', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('title', self.gf('django.db.models.fields.CharField')(unique=True, max_length=60)),
            ('chart_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['bmsapp.MultiBuildingChartType'])),
            ('parameters', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('sort_order', self.gf('django.db.models.fields.IntegerField')(default=999)),
        ))
        db.send_create_signal(u'bmsapp', ['MultiBuildingChart'])

        # Adding model 'ChartBuildingInfo'
        db.create_table(u'bmsapp_chartbuildinginfo', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('chart', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['bmsapp.MultiBuildingChart'])),
            ('building', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['bmsapp.Building'])),
            ('parameters', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('sort_order', self.gf('django.db.models.fields.IntegerField')(default=999)),
        ))
        db.send_create_signal(u'bmsapp', ['ChartBuildingInfo'])


    def backwards(self, orm):
        # Deleting model 'SensorGroup'
        db.delete_table(u'bmsapp_sensorgroup')

        # Deleting model 'Unit'
        db.delete_table(u'bmsapp_unit')

        # Deleting model 'Sensor'
        db.delete_table(u'bmsapp_sensor')

        # Deleting model 'BuildingChartType'
        db.delete_table(u'bmsapp_buildingcharttype')

        # Deleting model 'MultiBuildingChartType'
        db.delete_table(u'bmsapp_multibuildingcharttype')

        # Deleting model 'Building'
        db.delete_table(u'bmsapp_building')

        # Deleting model 'BldgToSensor'
        db.delete_table(u'bmsapp_bldgtosensor')

        # Deleting model 'BuildingChart'
        db.delete_table(u'bmsapp_buildingchart')

        # Deleting model 'MultiBuildingChart'
        db.delete_table(u'bmsapp_multibuildingchart')

        # Deleting model 'ChartBuildingInfo'
        db.delete_table(u'bmsapp_chartbuildinginfo')


    models = {
        u'bmsapp.bldgtosensor': {
            'Meta': {'ordering': "('building__title', 'sensor_group__sort_order', 'sort_order')", 'object_name': 'BldgToSensor'},
            'building': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['bmsapp.Building']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'sensor': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['bmsapp.Sensor']"}),
            'sensor_group': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['bmsapp.SensorGroup']"}),
            'sort_order': ('django.db.models.fields.IntegerField', [], {'default': '999'})
        },
        u'bmsapp.building': {
            'Meta': {'ordering': "['title']", 'object_name': 'Building'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'sensors': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': u"orm['bmsapp.Sensor']", 'null': 'True', 'through': u"orm['bmsapp.BldgToSensor']", 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '50'})
        },
        u'bmsapp.buildingchart': {
            'Meta': {'ordering': "['sort_order']", 'object_name': 'BuildingChart'},
            'building': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['bmsapp.Building']"}),
            'chart_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['bmsapp.BuildingChartType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'parameters': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'sort_order': ('django.db.models.fields.IntegerField', [], {'default': '999'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '60'})
        },
        u'bmsapp.buildingcharttype': {
            'Meta': {'ordering': "['sort_order']", 'object_name': 'BuildingChartType'},
            'class_name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'sort_order': ('django.db.models.fields.IntegerField', [], {'default': '999'}),
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