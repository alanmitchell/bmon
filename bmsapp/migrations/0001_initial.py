# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='BldgToSensor',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('sort_order', models.IntegerField(default=999)),
            ],
            options={
                'ordering': ('building__title', 'sensor_group__sort_order', 'sort_order'),
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Building',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(unique=True, max_length=50)),
                ('latitude', models.FloatField(default=62.0)),
                ('longitude', models.FloatField(default=-161.0)),
                ('timezone', models.CharField(default=b'US/Alaska', max_length=50, verbose_name=b'Time Zone of Facility, from tz database')),
                ('schedule', models.TextField(verbose_name=b'Occupied Schedule of Facility (e.g. M-F: 8a-5p)', blank=True)),
            ],
            options={
                'ordering': ['title'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='BuildingGroup',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(unique=True, max_length=50)),
                ('sort_order', models.IntegerField(default=999)),
                ('buildings', models.ManyToManyField(to='bmsapp.Building')),
            ],
            options={
                'ordering': ['sort_order', 'title'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ChartBuildingInfo',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('parameters', models.TextField(verbose_name=b'Chart Parameters in Keyword Form', blank=True)),
                ('sort_order', models.IntegerField(default=999)),
                ('building', models.ForeignKey(to='bmsapp.Building')),
            ],
            options={
                'ordering': ['sort_order'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='DashboardItem',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('widget_type', models.CharField(default=b'gauge', max_length=15, choices=[(b'gauge', b'Gauge'), (b'LED', b'Red/Green LED'), (b'label', b'Label')])),
                ('row_number', models.IntegerField(default=1)),
                ('column_number', models.IntegerField(default=1)),
                ('title', models.CharField(max_length=50, null=True, verbose_name=b'Widget Title (can be blank)', blank=True)),
                ('minimum_normal_value', models.FloatField(default=0.0)),
                ('maximum_normal_value', models.FloatField(default=100.0)),
                ('minimum_axis_value', models.FloatField(null=True, blank=True)),
                ('maximum_axis_value', models.FloatField(null=True, blank=True)),
                ('generate_alert', models.BooleanField(default=False)),
                ('no_alert_start_date', models.DateField(null=True, verbose_name=b'Except from', blank=True)),
                ('no_alert_end_date', models.DateField(null=True, verbose_name=b'to', blank=True)),
                ('building', models.ForeignKey(to='bmsapp.Building')),
                ('sensor', models.ForeignKey(blank=True, to='bmsapp.BldgToSensor', null=True)),
            ],
            options={
                'ordering': ('row_number', 'column_number', 'sensor__sort_order'),
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='MultiBuildingChart',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(unique=True, max_length=60)),
                ('parameters', models.TextField(verbose_name=b'General Chart Parameters in Keyword Form', blank=True)),
                ('sort_order', models.IntegerField(default=999)),
            ],
            options={
                'ordering': ['sort_order'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='MultiBuildingChartType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(unique=True, max_length=50)),
                ('class_name', models.CharField(unique=True, max_length=60)),
                ('sort_order', models.IntegerField(default=999)),
            ],
            options={
                'ordering': ['sort_order'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Sensor',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('sensor_id', models.CharField(unique=True, max_length=30, verbose_name=b'Monnit Sensor ID, or Calculated Field ID')),
                ('title', models.CharField(max_length=50)),
                ('is_calculated', models.BooleanField(default=False, verbose_name=b'Calculated Field')),
                ('tran_calc_function', models.CharField(max_length=35, verbose_name=b'Transform or Calculated Field Function Name', blank=True)),
                ('function_parameters', models.TextField(verbose_name=b'Function Parameters in Keyword form', blank=True)),
                ('calculation_order', models.IntegerField(default=0)),
            ],
            options={
                'ordering': ['sensor_id'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='SensorGroup',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(unique=True, max_length=40)),
                ('sort_order', models.IntegerField(default=999)),
            ],
            options={
                'ordering': ['sort_order'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Unit',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('label', models.CharField(unique=True, max_length=20, verbose_name=b'Unit Label')),
                ('measure_type', models.CharField(max_length=30, verbose_name=b'Measurement Type')),
            ],
            options={
                'ordering': ['measure_type', 'label'],
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='sensor',
            name='unit',
            field=models.ForeignKey(to='bmsapp.Unit'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='multibuildingchart',
            name='chart_type',
            field=models.ForeignKey(to='bmsapp.MultiBuildingChartType'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='chartbuildinginfo',
            name='chart',
            field=models.ForeignKey(to='bmsapp.MultiBuildingChart'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='building',
            name='sensors',
            field=models.ManyToManyField(to='bmsapp.Sensor', null=True, through='bmsapp.BldgToSensor', blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='bldgtosensor',
            name='building',
            field=models.ForeignKey(to='bmsapp.Building'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='bldgtosensor',
            name='sensor',
            field=models.ForeignKey(to='bmsapp.Sensor'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='bldgtosensor',
            name='sensor_group',
            field=models.ForeignKey(to='bmsapp.SensorGroup'),
            preserve_default=True,
        ),
    ]
