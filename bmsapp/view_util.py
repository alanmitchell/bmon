'''
Helper functions for the views in this BMS application.
'''
import importlib
import os
from subprocess import check_output
from django.template import loader
from django.templatetags.static import static

from . import models
from bmsapp.reports import basechart
import markdown
import time, json, re

def to_int(val):
    '''
    Trys to convert 'val' to an integer and returns the integer.  If 'val' is not an integer,
    just returns the original 'val'.
    '''
    try:
        return int(val)
    except:
        return val

def buildings_for_organization(org_id):
    """Returns a list of building objects that are in the Organization
    identified by 'org_id'. An org_id of 0 indicates All Buildings.
    """
    return models.Building.objects.all() if org_id==0 else \
        models.Building.objects.filter(organization__pk=org_id)

def groups_for_organization(org_id):
    """Returns a list of building groups that are in the Organization
    identified by 'org_id'. An org_id of 0 indicates All groups.
    """
    return models.BuildingGroup.objects.all() if org_id==0 else \
        models.BuildingGroup.objects.filter(organization__pk=org_id)

def buildings_for_group(group_id):
    """Returns a list of building objects that are in the group identified by 
    'group_id'.  A group_id of 0 indicates All Buildings.
    """

    return models.Building.objects.all() if group_id==0 else \
        models.Building.objects.filter(buildinggroup__pk=group_id)


def multi_charts_for_org(org_id):
    """Returns a list of MultiBuildingChart objects associated with the 
    Organization indicated by 'org_id'. 
    """
    if org_id != 0:
        return models.Organization.objects.get(id=org_id).multi_charts.all()
    else:
        # All organizations requested, so return all multi-building charts.
        return models.MultiBuildingChart.objects.all()
    
def organization_list_html():
    """Returns the html for the organization list options and also returns
    the ID of the first organization in the list, "All Organizations", which
    is selected.
    """
    # always have the All Organziations option, which has the special id of 0.
    orgs = [ (0, 'All Organizations', '') ]
    
    # add the rest of the organizations.
    for org in models.Organization.objects.all():
        orgs.append( (org.id, org.title, '') )
        
    # Selected organization is the first one
    selected_org = orgs[0][0]
    
    t = loader.get_template('bmsapp/select_list.html')
    return t.render( {'item_list': orgs, 'id_to_select': selected_org} ), selected_org

def group_list_html(org_id):
    """Returns the html for the building group list options associated with
    the Organization with ID of 'org_id'. Also returns the
    ID of the first group, which is selected.
    """
    # always have the All Buildings option, which has the special id of 0.
    groups = [ (0, 'All Facilities', '') ]
    
    # add the rest of the groups.
    for gp in groups_for_organization(org_id):
        groups.append( (gp.id, gp.title, '') )
        
    # Selected group is the first one
    selected_gp = groups[0][0]
    
    t = loader.get_template('bmsapp/select_list.html')
    return t.render( {'item_list': groups, 'id_to_select': selected_gp} ), selected_gp


def bldg_list_html(org_id, bldg_group_id, selected_bldg_id=None):
    '''
    Makes the html for the building list options and also returns the ID of the 
    building that is selected.  'org_id' is the primary key of the Organization
    that filters the building list.  The list is further filtered by 
    'bldg_group_id', which is the primary key
    ID of the building group.  A pk=0 means
    that All buildings are to be included.
    If 'selected_bldg_id' is not None, that building is selected in the list, 
    otherwise the first building in the list is selected.
    '''
    bldgs = []

    # Determine whether a Multi building chart selection should be presented.
    if len(multi_charts_for_org(org_id)):
        bldgs.append( ('multi', 'Multiple Buildings', '') )
    
    # Get intersection of buildings in organization and buildings in group
    more_bldgs = set(buildings_for_organization(org_id)) & set(buildings_for_group(bldg_group_id))
    # sort these according to title
    more_bldgs = list(more_bldgs)
    more_bldgs.sort(key=lambda x: x.title)

    # Add the rest of buildings that are in the group
    for bldg in more_bldgs:
        bldgs.append( (bldg.id, bldg.title, '') )

    if selected_bldg_id==None and len(bldgs)>0:
        selected_bldg_id = bldgs[0][0] 

    t = loader.get_template('bmsapp/select_list.html')
    return t.render( {'item_list': bldgs, 'id_to_select': selected_bldg_id} ), selected_bldg_id


def chart_list_html(org_id, bldg_id):
    '''
    Makes the html for the chart list options and also returns the ID of the 
    selected chart, which is the first chart in the list.
    'bldg_id' is the ID of the of building to list charts for, or it is the string 
        'multi' indicating that the multi-building charts should be listed.
    'org_id' is the ID of the Organization currently in effect.  If 'bldg_id'
    is 'multi', only multi-building charts relevant to 'org_id' are shown.
    '''
    if bldg_id != 'multi':
        # check to see if there are any Dashboard items
        bldg_object = models.Building.objects.get(id=bldg_id)
        if len(bldg_object.dashboarditem_set.all()):
            # include Dashboard in chart list
            cht_list = basechart.BLDG_CHART_TYPES
        else:
            # exclude Dashboard chart.
            cht_list = basechart.BLDG_CHART_TYPES[:]  # All items
            for cht in cht_list:
                if cht.class_name == 'dashboard.Dashboard':
                    cht_list.remove(cht)
                    break
    else:
        cht_list = multi_charts_for_org(org_id)

    # Get the id of the first chart in the list and also make a generic
    # item list.
    id_to_select = cht_list[0].id
    item_list = []
    for cht in cht_list:
        # need to get the class for the chart so the data attributes that
        # need to be passed to the client can be found.
        class_name = cht.chart_class if bldg_id=='multi' else cht.class_name

        # class_name is in the format <module name>.<class name>; break it apart.
        mod_name, bare_class_name = class_name.split('.')
        mod = importlib.import_module('bmsapp.reports.%s' % mod_name.strip())
        
        # get a reference to the class referred to by class_name, and get
        # data atrributes from class
        chart_class = getattr(mod, bare_class_name.strip())
        attrs = chart_class.data_attributes()
        
        item_list.append( (cht.id, cht.title, attrs) )

    t = loader.get_template('bmsapp/select_list.html')
    return t.render( {'item_list': item_list, 'id_to_select': id_to_select} ), id_to_select

def sensor_list_html(bldg_id):
    """Returns the option list HTML for a Select control that allows 
    selection of a sensor(s) associated with the 'bldg_id' building.
    The first sensor is selected.  If 'bldg_id' is 'multi' then return
    no option elements.
    """

    if bldg_id == 'multi':
        return ''   # no sensors for multi-building reports and charts.

    # get the building model object for this building
    bldg_object = models.Building.objects.get(id=bldg_id)

    html = ''
    grp = ''    # tracks the sensor group
    first_sensor = True
    for b_to_sen in bldg_object.bldgtosensor_set.all():
        if b_to_sen.sensor_group != grp:
            if first_sensor == False:
                # Unless this is the first group, close the prior group
                html += '</optgroup>'
            html += '<optgroup label="%s">' % b_to_sen.sensor_group.title
            grp = b_to_sen.sensor_group
        html += '<option value="%s" %s>%s</option>' % \
            (b_to_sen.sensor.id, 'selected' if first_sensor else '', b_to_sen.sensor.title)
        first_sensor = False
    html += '</optgroup>'

    return html

def custom_reports(org_id):
    """Returns a sorted list of Custom Reports available for the organization identified
    by 'org_id'.
    """

    reports_list = []
    current_group = None
    group_reports = []

    # If the Organization has ID of 0, then that means all buildings and thus all
    # custom reports.  Otherwise just use the reports for the selected Organization.
    if org_id == 0:
        reports = models.CustomReport.objects.all()
    else:
        reports = models.Organization.objects.get(id=org_id).custom_reports.all()

    for report in reports:
        if report.group != current_group:
            if not current_group is None:
                reports_list.append((current_group,group_reports))
            current_group = report.group
            group_reports = []
        group_reports.append(report)

    if not current_group is None:
        reports_list.append((current_group,group_reports))
    else:
        reports_list.append(('Contact your BMON System Administrator to set up custom reports',[]))

    return reports_list

def custom_report_html(report_id):
    """Returns the content for a custom report.
    """
    report_info = models.CustomReport.objects.get(id=report_id)
    report_html = markdown.markdown(report_info.markdown_text)

    return report_html

def get_embedded_results_script(request, result):
    """Returns the javascript script to embed a report.
    """
    script_content = '''
(function(){
  var content = json_result_string;

  var scriptTag = document.querySelector(\'script[src$="request_path_string"]\');

  var newDiv = document.createElement("div");
  newDiv.innerHTML = content["html"];
  newDiv.style.cssText = scriptTag.style.cssText;
  newDiv.style.display = "flex";
  newDiv.style.flexDirection = "column";
  
  var reportLink = document.createElement("A");
  reportLink.text = "Go To Report";
  reportLink.href = "report_path_string";
  reportLink.style.textAlign = "right";
  newDiv.appendChild(reportLink);

  scriptTag.parentElement.replaceChild(newDiv, scriptTag);
'''
    script_content = script_content.replace('json_result_string',json.dumps(result)).replace('request_path_string',request.get_full_path())
    script_content = script_content.replace('json_result_string',json.dumps(result)).replace('report_path_string',request.build_absolute_uri(request.get_full_path().replace('/embed/','/')))

    if result["objects"]:
        script_content = 'var loadingDashboard;\n' + script_content
        script_content = 'var loadingPlotly;\n' + script_content
        script_content = 'var loadingjQuery;\n' + script_content
        script_content += '''

  var renderDashboard = (function(obj_config){
      // Load the dashboard script if undefined, and add the chart
      if ((typeof ANdash == 'undefined') || (typeof Gauge == 'undefined')) {
          if (!loadingDashboard) {
            loadingDashboard = true;
            console.log('loading dashboard')

            var dashboard_css = document.createElement('link');
            dashboard_css.rel = 'stylesheet';
            dashboard_css.type = 'text/css';
            dashboard_css.href = 'dashboard_css_url';
            document.getElementsByTagName('head')[0].appendChild(dashboard_css);

            var dashboard_script = document.createElement('script');
            dashboard_script.src = 'dashboard_script_url';
            document.getElementsByTagName('head')[0].appendChild(dashboard_script);

            var gauge_script = document.createElement('script');
            gauge_script.src = 'gauge_script_url';
            document.getElementsByTagName('head')[0].appendChild(gauge_script);
          }
          console.log('waiting for dashboard')
          setTimeout(renderDashboard, 100);
      } else if (typeof Plotly == 'undefined') {
          if (!loadingPlotly) {
            console.log('loading plotly')
            loadingPlotly = true;

            var plotly_script = document.createElement('script');
            plotly_script.src = '//cdn.plot.ly/plotly-latest.min.js';
            document.getElementsByTagName('head')[0].appendChild(plotly_script);
          }
          console.log('waiting for plotly')
          setTimeout(renderDashboard, 100);
      } else if (typeof jQuery == 'undefined') {
          if (!loadingjQuery) {
            console.log('loading jQuery')
            loadingjQuery = true;

            var jQuery_script = document.createElement('script');
            jQuery_script.src = '//code.jquery.com/jquery-1.11.2.min.js';
            document.getElementsByTagName('head')[0].appendChild(jQuery_script);
          }
          console.log('waiting for jQuery')
          setTimeout(renderDashboard, 100);
      } else {
        var renderTo = newDiv.querySelector('#'+obj_config.renderTo);
        ANdash.createDashboard(obj_config, renderTo);
        renderTo.removeAttribute("id");
      }});

  var drawGraph = (function(obj_config){
      // Load the Plotly script if undefined, and add the chart
      if (typeof Plotly == 'undefined') {
          if (!loadingPlotly) {
            console.log('loading plotly')
            loadingPlotly = true;

            var plotly_script = document.createElement('script');
            plotly_script.src = '//cdn.plot.ly/plotly-latest.min.js';
            document.getElementsByTagName('head')[0].appendChild(plotly_script);
          }
          console.log('waiting for plotly')
          setTimeout(drawGraph, 100);
      } else {
        var renderTo = newDiv.querySelector('#'+obj_config.renderTo);
        Plotly.plot(renderTo, obj_config.data, obj_config.layout, obj_config.config);
        renderTo.removeAttribute("id");
      }});

  // render each object in the content
  content['objects'].forEach( function(obj) { 
     switch (obj[0]) {
       case 'plotly':
         drawGraph(obj[1]);
         break;
       case 'dashboard':
         renderDashboard(obj[1]);
         break;
     }
  } );
'''
        script_content = script_content.replace('dashboard_css_url',request.build_absolute_uri(static('bmsapp/css/dashboard.css')) + '?t=' + str(int(time.time())))
        script_content = script_content.replace('dashboard_script_url',request.build_absolute_uri(static('bmsapp/scripts/dashboard.js')) + '?t=' + str(int(time.time())))
        script_content = script_content.replace('gauge_script_url',request.build_absolute_uri(static('bmsapp/scripts/gauge.min.js')))

    script_content += '})();' #close the javascript function declaration
    return script_content

def version_date_string():
    """This returns the date/time in string format of the 
    last commit in the git repo where this code is contained.
    If any error occurs, an empty string is returned.
    """
    ver_date = ''
    try:
        # Need to move into directory where this code is located to execute Git command
        dir_git = os.path.dirname(__file__)
        result = check_output('cd %s; git log -n1' % dir_git, shell=True)
        result = result.decode('utf-8')   # convert to string
        for lin in result.splitlines():
            if lin.startswith('Date:'):
                ver_date = lin[5:].strip()
                break
    except:
        pass

    return ver_date