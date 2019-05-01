# controls whether results are updated automatically or manually by
# a direct call to 'update_results'
_auto_recalc = true

# flags whether inputs are in the process of being loaded
_loading_inputs = false

# Called when inputs that affect the results have changed
inputs_changed = ->
  if _auto_recalc and not _loading_inputs
    # update the window location url if needed
    if urlQueryString() == ''
      history.replaceState(null,null,"?".concat(serializedInputs()))
    else if serializedInputs() != urlQueryString()
      history.pushState(null,null,"?".concat(serializedInputs()))
    # update the results display
    update_results() 

serializedInputs = ->
  $("select, input").serialize()
  
# Updates the results portion of the page
update_results = ->
  $("body").css "cursor", "wait"    # show hourglass

  $.getJSON($("#BaseURL").text() + "reports/results/", serializedInputs()).done((results) -> 
    # load the returned HTML into the results div, but empty first to ensure
    # event handlers, etc. are removed
    $("body").css "cursor", "default"   # remove hourglass cursor
    $("#results").empty()
    $("#results").html results.html
    
    # Loop through the returned JavaScript objects to create and make them
    $.each results.objects, (ix, obj) ->
      [obj_type, obj_config] = obj
      switch obj_type
        when 'plotly'
          Plotly.plot(obj_config.renderTo, obj_config.data, obj_config.layout, obj_config.config)
        when 'dashboard'
          ANdash.createDashboard(obj_config)
  ).fail (jqxhr, textStatus, error) ->
    $("body").css "cursor", "default"   # remove hourglass cursor
    err = textStatus + ", " + error
    alert "Error Occurred: " + err

# copies a link to embed the current report into another page
get_embed_link = ->
  title = document.getElementById("report_title")
  if title != null
    link_comment = "<!--- Embedded BMON Chart: #{title.innerText} --->"
  else
    link_comment = "<!--- Embedded BMON Chart --->"
  link_text = '<script src="' + $("#BaseURL").text() + 'reports/embed/' + '?' + serializedInputs() + '" async></script>'
  link_dialog = $("<div class='popup' title='Copy and paste this text to embed this view in a Custom Report:'><textarea id='embed_link' rows=5 style='width: 99%;font-size: 85%;resize: vertical'>#{link_comment}&#010;#{link_text}&#010;</textarea></div>")

  #link_dialog.text("#{link_comment}#{link_text}")
  link_dialog.dialog({
      modal: true
      width: 750
      buttons: {
        "Copy to Clipboard": ->
          $("#embed_link").select()
          success = document.execCommand("copy")
      }
      close: -> $(this).dialog('destroy').remove()
    })
  
# Sets the visibility of elements in the list of ids 'ctrl_list'.
# If 'show' is true then the element is shown, hidden otherwise.
set_visibility = (ctrl_list, show) ->
  for ctrl in ctrl_list
    element = document.getElementById($.trim(ctrl))
    if show
      $(element).show().find("select, input:visible").prop( "disabled", false )
    else
      $(element).hide().find("select, input").prop( "disabled", true )
  show

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
    'ctrl_normalize', 'ctrl_occupied', 'xy_controls', 'time_period_group', 'download_many'], false)

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
update_chart_sensor_lists = (event) ->
  # load the options from a AJAX query for the selected building
  url = "#{$("#BaseURL").text()}chart-sensor-list/#{$("#select_org").val()}/#{$("#select_bldg").val()}/"
  $.ajax
    url: url
    dataType: "json"
    async: not _loading_inputs
    success: (data) ->
      $("#select_chart").html(data.charts)
      $("#select_sensor").html(data.sensors)
      $("#select_sensor_x").html(data.sensors)
      $("#select_sensor_y").html(data.sensors)
      process_chart_change()

# Updates the list of building groups associated with the Organization selected.
update_group_list = ->
  # load the group choices from a AJAX query for the selected organization
  url = "#{$("#BaseURL").text()}group-list/#{$("#select_org").val()}/"
  $.ajax
    url: url
    dataType: "html"
    async: not _loading_inputs
    success: (data) ->
      $("#select_group").html(data)
      if not _loading_inputs
        # trigger the change event of the building selector to get the 
        # selected option to process.
        $("#select_group").trigger "change"

# Updates the list of buildings associated with the Building Group selected.
update_bldg_list = ->
  # load the building choices from a AJAX query for the selected building group
  url = "#{$("#BaseURL").text()}bldg-list/#{$("#select_org").val()}/#{$("#select_group").val()}/"
  $.ajax
    url: url
    dataType: "html"
    async: not _loading_inputs
    success: (data) ->
      $("#select_bldg").html(data)
      if not _loading_inputs
        # trigger the change event of the building selector to get the 
        # selected option to process.
        $("#select_bldg").trigger "change"

# handle the history.popstate event
$(window).on "popstate", (event) ->
  handleUrlQuery()
  update_results()

# extract the query string portion of the current window's url
urlQueryString = () ->
  url = window.location.href
  queryStart = url.indexOf('?') + 1
  if queryStart > 0
    url.substr(queryStart)
  else
    ''

# parse and handle the url query string
handleUrlQuery = () ->
    params = {}
    $.each urlQueryString().replace(/\+/g, '%20').split('&'), ->
      name_value = @split('=')
      name = decodeURIComponent(name_value[0])
      value = if name_value.length > 1 then decodeURIComponent(name_value[1]) else null
      if !(name of params)
        params[name] = []
      params[name].push value
      return
      
    # sort the params so their events fire properly
    sortedNames = do ->
      names = ['select_org', 'select_group','select_bldg','select_chart']
      for name of params
        if name not in names
          names.push name
      names
      
    # update control values
    _loading_inputs = true
    for name in sortedNames
      element = $('[name=\'' + name + '\']')
      if params.hasOwnProperty(name)
        new_value = params[name]
        if element[0].getAttribute("type") == "radio"
          old_value = element.filter(":radio:checked").val()
        else
          old_value = element.val()
        if `old_value != new_value`
          element.val(new_value)
          if element.attr("multiple") == "multiple"
            element.multiselect("refresh")
      element.change() # trigger the change event
    _loading_inputs = false
    params
  
# ---------------------------------------------------------------
# function that runs when the document is ready.
$ ->

  # Related to selecting the range of dates to chart
  $('#start_date').datepicker uiLibrary: 'bootstrap4'
  $('#end_date').datepicker uiLibrary: 'bootstrap4'

  d = new Date() # current date to use for a default for Start Date
  $("#start_date").val (d.getMonth() + 1) + "/" + d.getDate() + "/" + d.getFullYear()
  
  # Show and Hide custom date range selector
  $("#time_period").change ->
    unless $("input:radio[name=time_period]:checked").val() is "custom"
      $("#custom_dates").hide().find("select, input").prop( "disabled", true )
    else
      $("#custom_dates").show().find("select, input").prop( "disabled", false )
  $("#time_period").change()
  
  # make refresh button a jQuery button & call update when clicked
  $("#refresh").click update_results
  $("#get_embed_link").click get_embed_link     
  $("#div_date").datepicker uiLibrary: 'bootstrap4'   # for xy plot

  # special handling of the Excel Export button because the content for this report
  # is not displayed in a normal results div.
  $("#download_many").button().click ->
    window.location.href = "#{$("#BaseURL").text()}reports/results/?" + 
      serializedInputs();

  # Set up controls and functions to respond to events
  $("#select_org").change update_bldg_list
  $("#select_org").change update_group_list
  $("#select_group").change update_bldg_list
  $("#select_bldg").change update_chart_sensor_lists
  $("#select_chart").change process_chart_change

  # Set up change handlers for inputs.
  ctrls = ['averaging_time', 'averaging_time_export', 'normalize', 'show_occupied', 
    'select_sensor', 'select_sensor_x', 'select_sensor_y', 'averaging_time_xy', 'div_date']
  $("##{ctrl}").change inputs_changed for ctrl in ctrls

  # Special change handling of the time period radio inputs.
  $(document).on 'change', 'input:radio[name="time_period"]', inputs_changed

  # Handle any query parameters on the url
  handleUrlQuery()
  
  # Update the window's url to reflect the current inputs state
  history.replaceState(null,null,"?".concat(serializedInputs()))
  
  # Update the display based on the inputs
  inputs_changed()