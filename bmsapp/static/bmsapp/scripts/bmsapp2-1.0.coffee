# my object to contain all global variables and functions.  Minimizes
# global namespace pollution.
window.AN = {}

# Updates the results portion of the page
update_results = ->
  null

# Sets the visibility of elements in the list of ids 'ctrl_list'.
# If 'show' is true then the element is shown, hidden otherwise.
set_visibility = (ctrl_list, show) ->
  if show
    $("##{ctrl}").show() for ctrl in ctrl_list
  else
    $("##{ctrl}").hide() for ctrl in ctrl_list

# Handles actions required when the chart type changes.  Mostly sets
# the visibility of controls.
process_chart_change = ->
  # List of all input controls
  ctrls = ['refresh', 'ctrl_sensor', 'ctrl_avg', 'ctrl_avg_export', 'ctrl_normalize',
    'xy_controls', 'time_period', 'download_many']

  # start by hiding all inputs controls
  set_visibility(ctrls, false)

  # special case of the multi-building 
  if $("#select_bldg").val() == "multi"
    set_visibility(['refresh', 'time_period'], true)
    update_results()
    return

  # selectively show the needed controls for this chart
  is_multiple = false    # determines if sensor selector is multi-select
  switch $("#select_chart").val()
    when "0", "1"    # Dashboard and Current Values
      set_visibility(['refresh'], true)
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
      set_visibility(['refresh', 'ctrl_sensor', 'ctrl_avg_export', 
        'time_period', 'download_many'], true)
      is_multiple = true

  # Set the sensor selector to multiple or single select
  sensor_ctrl = $("#select_sensor")
  if is_multiple
    unless sensor_ctrl.attr("multiple") is "multiple"
      sensor_ctrl.attr("multiple", "multiple")
      sensor_ctrl.multiselect {minWidth: 300, selectedList: 3}
  else
    if sensor_ctrl.attr("multiple") == "multiple"
      sensor_ctrl.multiselect "destroy"
      sensor_ctrl.removeAttr "multiple"

  update_results()

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

# function that runs when the document is ready.
$ ->
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

  $("#refresh").button()     # make refresh button a jQuery button
  $("#normalize").button()   # checkbox to create normalized (0-100%) hourly profile
  $("#divide_date").datepicker dateFormat: "mm/dd/yy"   # for xy plot
  $("#download_many").button()   # export to Excel Button

  # Set up controls and functions to respond to events
  $("#select_group").change update_bldg_list
  $("#select_bldg").change update_chart_sensor_lists
  $("#select_chart").change process_chart_change

  # Process the currently selected chart
  process_chart_change()
