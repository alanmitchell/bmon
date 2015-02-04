# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('bmsapp', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='sensor',
            name='formatting_function',
            field=models.CharField(max_length=50, verbose_name=b'Formatting Function Name', blank=True),
            preserve_default=True,
        ),
    ]
