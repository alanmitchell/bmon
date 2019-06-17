#!/usr/local/bin/python3.7
'''Upgrades the Custom Reports model objects from the old Python 2.7
version of BMON to the Python 3.7 version (which also utilizes the
Bootstrap 4 framework, which causes most of the need to the following
changes.)
'''

import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "bmon.settings")
django.setup()

from bmsapp.models import CustomReport

for rpt in CustomReport.objects.all():
    txt = rpt.markdown_text
    txt_new = txt.replace(' style="width: 930px"', '')
    
    new_lines = []
    for lin in txt_new.splitlines():
        if 'select_chart=2' in lin:
            new_lin = lin.replace('select_sensor=', 'select_sensor_multi=')
        else:
            new_lin = lin
        new_lines.append(new_lin)

    rpt.markdown_text = '\n'.join(new_lines)
    rpt.save()
    print(rpt.markdown_text)
