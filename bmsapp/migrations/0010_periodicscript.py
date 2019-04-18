# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('bmsapp', '0009_auto_20160322_1730'),
    ]

    operations = [
        migrations.CreateModel(
            name='PeriodicScript',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('script_file_name', models.CharField(max_length=50, verbose_name=b'File name of script')),
                ('period', models.IntegerField(default=3600, verbose_name=b'How often should script run', choices=[(300, b'5 min'), (600, b'10 min'), (900, b'15 min'), (1800, b'30 min'), (3600, b'1 hr'), (7200, b'2 hr'), (14400, b'4 hr'), (21600, b'6 hr'), (43200, b'12 hr'), (86400, b'24 hr')])),
                ('script_parameters', models.TextField(verbose_name=b'Script Parameters in YAML form', blank=True)),
                ('script_results', models.TextField(verbose_name=b'Script results in YAML form', blank=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
