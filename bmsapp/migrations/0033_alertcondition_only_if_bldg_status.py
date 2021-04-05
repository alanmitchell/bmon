# Generated by Django 2.2.4 on 2021-04-02 22:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bmsapp', '0032_auto_20190926_1206'),
    ]

    operations = [
        migrations.AddField(
            model_name='alertcondition',
            name='only_if_bldg_status',
            field=models.CharField(blank=True, choices=[('Occupied', 'Occupied'), ('Unoccupied', 'Unoccupied')], max_length=15, null=True, verbose_name='and this status'),
        ),
    ]
