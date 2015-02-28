# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('bmsapp', '0002_auto_20150224_0702'),
    ]

    operations = [
        migrations.CreateModel(
            name='AlertCondition',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('active', models.BooleanField(default=True, help_text=b'Uncheck the box to Disable the alert.')),
                ('condition', models.CharField(default=b'>', max_length=20, verbose_name=b'Notify when the Sensor value is', choices=[(b'>', b'>'), (b'>=', b'>='), (b'<', b'<'), (b'<=', b'<='), (b'==', b'equal to'), (b'!=', b'not equal to'), (b'inactive', b'inactive')])),
                ('test_value', models.FloatField(null=True, verbose_name=b'this value', blank=True)),
                ('alert_message', models.TextField(help_text=b'If left blank, a message will be created.  Use the string "{val}" in the message to show the current sensor value.', max_length=200, blank=True)),
                ('priority', models.CharField(default=b'0', max_length=5, verbose_name=b'Priority of this Alert Situation', choices=[(b'-1', b'Low'), (b'0', b'Normal'), (b'1', b'High'), (b'2', b'Emergency')])),
                ('wait_before_next', models.FloatField(default=4.0, verbose_name=b'Hours to Wait before Notifying Again')),
                ('last_notified', models.FloatField(default=0.0)),
                ('only_if_bldg', models.ForeignKey(verbose_name=b'But only if building', blank=True, to='bmsapp.Building', null=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='AlertRecipient',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('active', models.BooleanField(default=True)),
                ('name', models.CharField(max_length=50)),
                ('notify_email', models.BooleanField(default=True, verbose_name=b'Send Email?')),
                ('email_address', models.EmailField(max_length=100, blank=True)),
                ('notify_cell', models.BooleanField(default=True, verbose_name=b'Send Text Message?')),
                ('cell_number', models.CharField(blank=True, max_length=10, verbose_name=b'10 digit Cell number', validators=[django.core.validators.RegexValidator(regex=b'^\\d{10}$', message=b'Phone number must be entered as a 10 digit number, including area code, no spaces, dashes or parens.')])),
                ('cell_sms_gateway', models.CharField(blank=True, max_length=60, verbose_name=b'Cell Phone Carrier', choices=[(b'msg.acsalaska.com', b'Alaska Communications (ACS)'), (b'txt.att.net', b'AT&T'), (b'mobile.gci.net', b'General Communications Inc. (GCI)'), (b'sms.mtawireless.com', b'MTA Wireless'), (b'vtext.com', b'Verizon Wireless')])),
                ('notify_pushover', models.BooleanField(default=True, verbose_name=b'Send Pushover Notification?')),
                ('pushover_id', models.CharField(blank=True, max_length=30, verbose_name=b'Pushover ID', validators=[django.core.validators.RegexValidator(regex=b'^\\w{30}$', message=b'Pushover ID should be exactly 30 characters long.')])),
            ],
            options={
                'ordering': ['name'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='BuildingMode',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=50, verbose_name=b'Mode Name')),
            ],
            options={
                'ordering': ['name'],
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='alertcondition',
            name='only_if_bldg_mode',
            field=models.ForeignKey(verbose_name=b'is in this mode', blank=True, to='bmsapp.BuildingMode', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='alertcondition',
            name='recipients',
            field=models.ManyToManyField(to='bmsapp.AlertRecipient', null=True, verbose_name=b'Who should be notified?', blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='alertcondition',
            name='sensor',
            field=models.ForeignKey(to='bmsapp.Sensor'),
            preserve_default=True,
        ),
        migrations.RemoveField(
            model_name='dashboarditem',
            name='generate_alert',
        ),
        migrations.RemoveField(
            model_name='dashboarditem',
            name='no_alert_end_date',
        ),
        migrations.RemoveField(
            model_name='dashboarditem',
            name='no_alert_start_date',
        ),
        migrations.AddField(
            model_name='building',
            name='current_mode',
            field=models.ForeignKey(verbose_name=b'Current Operating Mode', blank=True, to='bmsapp.BuildingMode', null=True),
            preserve_default=True,
        ),
    ]
