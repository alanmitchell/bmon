# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('bmsapp', '0003_auto_20150302_1159'),
    ]

    operations = [
        migrations.AlterField(
            model_name='alertcondition',
            name='condition',
            field=models.CharField(default=b'>', max_length=20, verbose_name=b'Notify when the Sensor value is', choices=[(b'>', b'greater than'), (b'>=', b'greater than or equal to'), (b'<', b'less than'), (b'<=', b'less than or equal to'), (b'==', b'equal to'), (b'!=', b'not equal to'), (b'inactive', b'inactive')]),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='building',
            name='title',
            field=models.CharField(unique=True, max_length=80),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='buildinggroup',
            name='title',
            field=models.CharField(unique=True, max_length=80),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='sensor',
            name='sensor_id',
            field=models.CharField(unique=True, max_length=80, verbose_name=b'Monnit Sensor ID, or Calculated Field ID'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='sensor',
            name='title',
            field=models.CharField(max_length=80),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='sensorgroup',
            name='title',
            field=models.CharField(unique=True, max_length=80),
            preserve_default=True,
        ),
    ]
