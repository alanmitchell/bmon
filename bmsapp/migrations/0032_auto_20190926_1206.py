# Generated by Django 2.1.7 on 2019-09-26 20:06

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('bmsapp', '0031_auto_20190909_2040'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bldgtosensor',
            name='sensor_group',
            field=models.ForeignKey(default=8, on_delete=django.db.models.deletion.SET_DEFAULT, to='bmsapp.SensorGroup'),
        ),
    ]