# Generated by Django 2.2.28 on 2023-06-29 01:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bmsapp', '0036_auto_20230516_1554'),
    ]

    operations = [
        migrations.AlterField(
            model_name='building',
            name='latitude',
            field=models.FloatField(default=61.13),
        ),
        migrations.AlterField(
            model_name='building',
            name='longitude',
            field=models.FloatField(default=-150.63),
        ),
    ]
