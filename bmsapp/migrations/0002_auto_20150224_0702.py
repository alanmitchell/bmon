# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('bmsapp', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='sensor',
            name='tran_calc_function',
            field=models.CharField(max_length=80, verbose_name=b'Transform or Calculated Field Function Name', blank=True),
            preserve_default=True,
        ),
    ]
