# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('bmsapp', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='multibuildingchart',
            name='chart_type',
        ),
        migrations.DeleteModel(
            name='MultiBuildingChartType',
        ),
        migrations.AddField(
            model_name='multibuildingchart',
            name='chart_class',
            field=models.CharField(max_length=60, null=True, choices=[(b'currentvalues_multi.CurrentValuesMulti', b'Current Sensor Values'), (b'normalizedbyddbyft2.NormalizedByDDbyFt2', b'Energy / Degree-Day / ft2'), (b'normalizedbyft2.NormalizedByFt2', b'Energy / ft2')]),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='chartbuildinginfo',
            name='parameters',
            field=models.TextField(verbose_name=b'Chart Parameters in YAML Form', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='multibuildingchart',
            name='parameters',
            field=models.TextField(verbose_name=b'General Chart Parameters in YAML Form', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='sensor',
            name='function_parameters',
            field=models.TextField(verbose_name=b'Function Parameters in YAML form', blank=True),
            preserve_default=True,
        ),
    ]
