# Generated by Django 2.2.28 on 2023-01-18 02:44

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('bmsapp', '0034_building_notes_private'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='bldgtosensor',
            options={'ordering': ('building__title', 'sensor_group__sort_order', 'sensor_group__title', 'sort_order', 'sensor__title')},
        ),
    ]
