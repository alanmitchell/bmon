# Generated by Django 2.2.28 on 2024-03-13 17:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bmsapp', '0038_auto_20240312_0824'),
    ]

    operations = [
        migrations.AddField(
            model_name='alertrecipient',
            name='notes',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='alertrecipientgroup',
            name='notes',
            field=models.TextField(blank=True),
        ),
    ]
