# my object to contain all global variables and functions.  Minimizes
# global namespace pollution.
window.AN = {}

# Causes a particular chart type and sensor to be selected.
window.AN.plot_sensor = (chart_id, sensor_id) ->
    $("#select_chart").val chart_id 
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

# controls whether results are updated automatically or manually by
# a direct call to 'update_results'
_auto_recalc = true

# Called when inputs that affect the results have changed
inputs_changed = ->
  update_results() if _auto_recalc

# Updates the results portion of the page
update_results = ->
  url = "#{$("#BaseURL").text()}reports/results/"
  $.getJSON url, $("#content select, #content input").serialize(), (results) -> 
    # load the returned HTML into the results div
    $("#results").html results.html + '<p><pre>' + JSON.stringify(results.objects) + '</pre></p>'
    # Loop through the returned JavaScript objects to create and make them
    $.each results.objects, (ix, obj) ->
      [obj_type, obj_config] = obj
      switch obj_type
        when 'highchart' then new Highcharts.Chart(obj_config)
        when 'highstock' then new Highcharts.StockChart(obj_config)
        when 'dashboard' then ANdash.createDashboard(obj_config)

# Sets the visibility of elements in the list of ids 'ctrl_list'.
# If 'show' is true then the element is shown, hidden otherwise.
set_visibility = (ctrl_list, show) ->
  if show
    $("##{ctrl}").show() for ctrl in ctrl_list
  else
    $("##{ctrl}").hide() for ctrl in ctrl_list

# A timer used by some charts to do a timed refresh of the results.
REFRESH_MS = 600000  # milliseconds between timed refreshes
_refresh_timer = setInterval update_results, REFRESH_MS

# The configuration options for a the multiselect sensor input
SENSOR_MULTI_CONFIG = {minWidth: 300, selectedList: 3, close: inputs_changed}

# Handles actions required when the chart type changes.  Mostly sets
# the visibility of controls.
process_chart_change = ->

  # start by hiding all inputs controls
  set_visibility(['refresh', 'ctrl_sensor', 'ctrl_avg', 'ctrl_avg_export',
    'ctrl_normalize', 'xy_controls', 'time_period', 'download_many'], false)

  # As the default, clear timed refresh
  clearInterval _refresh_timer

  # default is automatic updating of results
  _auto_recalc = true

  # special case of the multi-building 
  if $("#select_bldg").val() == "multi"
    set_visibility(['refresh', 'time_period'], true)
    inputs_changed()
    return

  # Configure control visibility and other chart-related options
  is_multiple = false    # determines if sensor selector is multi-select
  switch $("#select_chart").val()
    when "0", "1"    # Dashboard and Current Values
      set_visibility(['refresh'], true)
      _refresh_timer = setInterval update_results, REFRESH_MS
    when "2"    # Time Series
      set_visibility(['refresh', 'ctrl_sensor', 'ctrl_avg', 'time_period'], true)
      is_multiple = true
    when "3"    # Hourly Profile
      set_visibility(['refresh', 'ctrl_sensor', 'ctrl_normalize', 'time_period'], true)
    when "4"    # Histogram
      set_visibility(['refresh', 'ctrl_sensor', 'time_period'], true)
    when "5"    # XY
      set_visibility(['refresh', 'xy_controls', 'time_period'], true)
    when "6"    # Excel Download
      set_visibility(['ctrl_sensor', 'ctrl_avg_export', 
        'time_period', 'download_many'], true)
      is_multiple = true
      _auto_recalc = false

  # Set the sensor selector to multiple or single select
  sensor_ctrl = $("#select_sensor")
  if is_multiple
    unless sensor_ctrl.attr("multiple") is "multiple"
      sensor_ctrl.off()   # remove any existing handlers
      sensor_ctrl.attr("multiple", "multiple")
      sensor_ctrl.multiselect SENSOR_MULTI_CONFIG
  else
    if sensor_ctrl.attr("multiple") == "multiple"
      sensor_ctrl.multiselect "destroy"
      sensor_ctrl.removeAttr "multiple"
      sensor_ctrl.off().change inputs_changed

  # the chart type changed so indicated that inputs have changed
  inputs_changed()

# Updates the list of charts and sensors appropriate for the building selected.
update_chart_sensor_lists = ->
  # load the options from a AJAX query for the selected building
  url = "#{$("#BaseURL").text()}chart_sensor_list/#{$("#select_group").val()}/#{$("#select_bldg").val()}/"
  $.getJSON url, (data) ->
    $("#select_chart").html(data.charts)
    $("#select_sensor").html(data.sensors)
    $("#select_sensor_x").html(data.sensors)
    $("#select_sensor_y").html(data.sensors)

    process_chart_change()

# Updates the list of buildings associated with the Building Group selected.
update_bldg_list = ->
  # load the building choices from a AJAX query for the selected building group
  $("#select_bldg").load "#{$("#BaseURL").text()}bldg_list/#{$("#select_group").val()}/", ->
    # trigger the change event of the building selector to get the 
    # selected option to process.
    $("#select_bldg").trigger "change"

# ---------------------------------------------------------------
# function that runs when the document is ready.
$ ->

  # Make Highcharts display in the timezone of the client's computer
  Highcharts.setOptions global:
    useUTC: false

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
  $("#normalize").button()   # checkbox to create normalized (0-100%) hourly profile
  $("#divide_date").datepicker dateFormat: "mm/dd/yy"   # for xy plot
  $("#download_many").button().click update_results   # export to Excel Button

  # Set up controls and functions to respond to events
  $("#select_group").change update_bldg_list
  $("#select_bldg").change update_chart_sensor_lists
  $("#select_chart").change process_chart_change

  # Set up change handlers for inputs.  Sensor select control is
  # special case and is set up in process_chart_change routine.
  ctrls = ['averaging_time', 'averaging_time_export', 'normalize', 'select_sensor_x',
    'select_sensor_y', 'averaging_time_xy', 'divide_date', 'time_period']
  $("##{ctrl}").change inputs_changed for ctrl in ctrls

  # Process the currently selected chart
  process_chart_change()
