"""Converts my original keyword parameters to YAML parameters
"""
import bmsapp.models
import yaml


def makeKeywordArgs(keyword_str):
    '''Original function to convert keyword string into dictionary, except special
    handling of 'id_' keywords was removed.
    '''
    result = {}
    keyword_str = keyword_str.strip()
    # need to exit if this is a blank string
    if len(keyword_str)==0:
        return result

    for it in keyword_str.strip().split(','):
        kw, val = it.split('=')
        kw = kw.strip()
        val = val.strip()
        try:
            val = float(val)
        except:
            if val in ('True', 'true', 'Y', 'y', 'Yes', 'yes'):
                val = True
            elif val in ('False', 'false', 'N', 'n', 'No', 'no'):
                val = False
            else:
                # must be a string.
                # get rid of surrounding quotes of both types.
                val = val.strip('"\'')

        result[kw] = val

    return result


def run():
    for sen in bmsapp.models.Sensor.objects.exclude(function_parameters=''):
        print sen.function_parameters
        obj = makeKeywordArgs(str(sen.function_parameters))
        sen.function_parameters = yaml.dump(obj, default_flow_style=False)
        sen.save()

    print 
    for sen in bmsapp.models.Sensor.objects.exclude(function_parameters=''):
        print sen.function_parameters
