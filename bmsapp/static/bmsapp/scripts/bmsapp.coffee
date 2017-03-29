# my object to contain all global variables and functions.  Minimizes
# global namespace pollution.
window.AN = {}

# Causes a particular chart type and sensor to be selected.  if 'sensor_id'
# is not passed, only the chart is selected.
window.AN.plot_sensor = (chart_id, sensor_id) ->
  $("#select_chart").val chart_id
  if sensor_id?
    sensor_ctrl = $("#select_sensor")
    if $("#select_sensor").attr("multiple") == "multiple"
      # had difficulty finding a simpler way to set the value of a 
      # multiselect.
      sensor_ctrl.multiselect "destroy"
      sensor_ctrl.removeAttr "multiple"
      sensor_ctrl.val sensor_id
      sensor_ctrl.attr("multiple", "multiple")
      sensor_ctrl.multiselect SENSOR_MULTI_CONFIG
    else
      sensor_ctrl.val sensor_id
  process_chart_change()

# Causes a particular building, chart and sensor to be selected.
# 'chart_id' and 'sensor_id' are optional; if both are omitted, only
# the building is selected.
window.AN.plot_building_chart_sensor = (bldg_id, chart_id, sensor_id) ->
  $("#select_bldg").val bldg_id
  update_chart_sensor_lists(null, chart_id, sensor_id)

# controls whether results are updated automatically or manually by
# a direct call to 'update_results'
_auto_recalc = true

# Called when inputs that affect the results have changed
inputs_changed = ->
  update_results() if _auto_recalc

# Updates the results portion of the page
update_results = ->
  $("body").css "cursor", "wait"    # show hourglass
  url = "#{$("#BaseURL").text()}reports/results/"
  $.getJSON(url, $("#content select, #content input").serialize()
  ).done((results) -> 
    # load the returned HTML into the results div, but empty first to ensure
    # event handlers, etc. are removed
    $("body").css "cursor", "default"   # remove hourglass cursor
    $("#results").empty()
    $("#results").html results.html
    # Loop through the returned JavaScript objects to create and make them
    $.each results.objects, (ix, obj) ->
      [obj_type, obj_config] = obj
      switch obj_type
        when 'plotly' then Plotly.plot(obj_config.renderTo, obj_config.data, obj_config.layout, obj_config.config)
        when 'dashboard' then ANdash.createDashboard(obj_config)
  ).fail (jqxhr, textStatus, error) ->
    $("body").css "cursor", "default"   # remove hourglass cursor
    err = textStatus + ", " + error
    alert "Error Occurred: " + err

# copies a link to embed the current report into another page
get_embed_link = ->
  link = '<script src="' + $("#BaseURL").text() + 'reports/embed/' + '?' + $("#content select, #content input").serialize() + '" style="width: 930px" async></script>'
  prompt("Here's the text to embed this report in another page:", link)
  
# Sets the visibility of elements in the list of ids 'ctrl_list'.
# If 'show' is true then the element is shown, hidden otherwise.
set_visibility = (ctrl_list, show) ->
  if show
    $("##{$.trim(ctrl)}").show() for ctrl in ctrl_list
  else
    $("##{$.trim(ctrl)}").hide() for ctrl in ctrl_list

# A timer used by some charts to do a timed refresh of the results.
REFRESH_MS = 600000  # milliseconds between timed refreshes
_refresh_timer = setInterval update_results, REFRESH_MS

# The configuration options for a the multiselect sensor input
SENSOR_MULTI_CONFIG = {minWidth: 300, selectedList: 3, close: inputs_changed}

# Handles actions required when the chart type changes.  Mostly sets
# the visibility of controls.
process_chart_change = ->

  # start by hiding all input controls
  set_visibility(['refresh', 'ctrl_sensor', 'ctrl_avg', 'ctrl_avg_export',
    'ctrl_normalize', 'ctrl_occupied', 'xy_controls', 'time_period', 'download_many'], false)

  # get the chart option control that is selected.  Then use the data
  # attributes of that option element to configure the user interface.
  selected_chart_option = $("#select_chart").find("option:selected")

  # list of controls that should be visible
  vis_ctrls = selected_chart_option.data("ctrls").split(",")
  set_visibility(vis_ctrls, true)

  # Should timed refresh be set?
  clearInterval _refresh_timer   # clear any old timer
  if selected_chart_option.data("timed_refresh") == 1
    _refresh_timer = setInterval update_results, REFRESH_MS
 
  # set auto recalculation
  _auto_recalc = (selected_chart_option.data("auto_recalc") == 1)

  # Set sensor selector to multiple if needed
  sensor_ctrl = $("#select_sensor")
  if selected_chart_option.data("multi_sensor") == 1
    unless sensor_ctrl.attr("multiple") is "multiple"
      sensor_ctrl.off()   # remove any existing handlers
      sensor_ctrl.attr("multiple", "multiple")
      sensor_ctrl.multiselect SENSOR_MULTI_CONFIG
  else
    if sensor_ctrl.attr("multiple") == "multiple"
      sensor_ctrl.multiselect "destroy"
      sensor_ctrl.removeAttr "multiple"
      sensor_ctrl.off().change inputs_changed

  # if manual recalc, then blank out the results area to clear our remnants
  # from last chart
  $("#results").empty() if _auto_recalc == false

  # the chart type changed so indicated that inputs have changed
  inputs_changed()

# Updates the list of charts and sensors appropriate for the building selected.
# If chart_id and sensor_id are passed, selects that chart and sensor after
# updating the list of apprpriate charts and sensors.
update_chart_sensor_lists = (event, chart_id, sensor_id) ->
  # load the options from a AJAX query for the selected building
  url = "#{$("#BaseURL").text()}chart-sensor-list/#{$("#select_group").val()}/#{$("#select_bldg").val()}/"
  $.getJSON url, (data) ->
    $("#select_chart").html(data.charts)
    $("#select_sensor").html(data.sensors)
    $("#select_sensor_x").html(data.sensors)
    $("#select_sensor_y").html(data.sensors)

    if chart_id?
      window.AN.plot_sensor(chart_id, sensor_id)
    else
      process_chart_change()

# Updates the list of buildings associated with the Building Group selected.
update_bldg_list = ->
  # load the building choices from a AJAX query for the selected building group
  $("#select_bldg").load "#{$("#BaseURL").text()}bldg-list/#{$("#select_group").val()}/", ->
    # trigger the change event of the building selector to get the 
    # selected option to process.
    $("#select_bldg").trigger "change"

# ---------------------------------------------------------------
# function that runs when the document is ready.
$ ->

  # enable jQuery UI tooltips
  $(document).tooltip()

  # Configure many of the elements that commonly appear in chart configuration
  # form.
  $("#time_period").buttonset()

  # Related to selecting the range of dates to chart
  $("#start_date").datepicker dateFormat: "mm/dd/yy"
  d = new Date() # current date to use for a default for Start Date
  $("#start_date").val (d.getMonth() + 1) + "/" + d.getDate() + "/" + d.getFullYear()
  $("#end_date").datepicker dateFormat: "mm/dd/yy"
  $("#custom_dates").hide 0 # hide custom dates element
  # Show and Hide custom date range selector
  $("#time_period").change ->
    unless $("input:radio[name=time_period]:checked").val() is "custom"
      $("#custom_dates").hide()
    else
      $("#custom_dates").show()

  # make refresh button a jQuery button & call update when clicked
  $("#refresh").button().click update_results
  $("#get_embed_link").click get_embed_link     
  $("#normalize").button()   # checkbox to create normalized (0-100%) hourly profile
  $("#show_occupied").button()   # checkbox to create normalized (0-100%) hourly profile
  $("#div_date").datepicker dateFormat: "mm/dd/yy"   # for xy plot

  # special handling of the Excel Export button because the content for this report
  # is not displayed in a normal results div.
  $("#download_many").button().click ->
    window.location.href = "#{$("#BaseURL").text()}reports/results/?" + 
      $("#content select, #content input").serialize();

  # Set up controls and functions to respond to events
  $("#select_group").change update_bldg_list
  $("#select_bldg").change update_chart_sensor_lists
  $("#select_chart").change process_chart_change

  # Set up change handlers for inputs.
  ctrls = ['averaging_time', 'averaging_time_export', 'normalize', 'show_occupied', 
    'select_sensor', 'select_sensor_x', 'select_sensor_y', 'averaging_time_xy', 'div_date', 
    'time_period']
  $("##{ctrl}").change inputs_changed for ctrl in ctrls

  # Process the currently selected chart
  process_chart_change()
