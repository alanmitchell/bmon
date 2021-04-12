# Need to use Coffeescript 1.x to maintain IE compatibility.
# controls whether results are updated automatically or manually by
# a direct call to 'update_results'
_auto_recalc = true

# flags whether inputs are in the process of being loaded
_loading_inputs = false

# Called when inputs that affect the results have changed
inputs_changed = ->
  # having trouble with multi-select refreshing
  if $('#select_sensor_multi').prop('disabled') == false
    $('#select_sensor_multi').selectpicker('refresh')
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
  
  # get lingering tooltips from prior result.  Hide them.
  $('#results [data-toggle="tooltip"]').tooltip('hide')   

  $.getJSON($("#BaseURL").text() + "reports/results/", serializedInputs()).done((results) -> 
    # load the returned HTML into the results div, but empty first to ensure
    # event handlers, etc. are removed
    $("body").css "cursor", "default"   # remove hourglass cursor
    $("#results").empty()
    $("#results").html results.html

    $('#results [data-toggle="tooltip"]').tooltip()

    # apply custom settings to bmon-sensor-id elements
    $("#results .bmon-sensor-id")
        .attr("data-toggle","tooltip")
        .attr("data-original-title", "Click to copy Sensor ID to Clipboard")
        .css("cursor","pointer")
        .tooltip()
        .click ->
            target = this;
            navigator.clipboard.writeText(target.innerText).then ->
                $(target)
                    .attr("data-original-title", "Copied Sensor ID to Clipboard!")
                    .tooltip('show')
                return
            return
        .on('hidden.bs.tooltip', ->
            $(this).attr("data-original-title", "Click to copy Sensor ID to Clipboard")
            return
        )
        

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
  $('#embed_link').text(link_comment + '\n' + link_text + '\n')
  
# Sets the visibility of elements in the list of ids 'ctrl_list'.
# If 'show' is true then the element is shown, hidden otherwise.
set_visibility = (ctrl_list, show) ->
  for ctrl in ctrl_list
    element = document.getElementById($.trim(ctrl))
    if show
      $(element).show().find("select, input:visible").prop( "disabled", false )
    else
      $(element).hide().find("select, input").prop( "disabled", true )
    $("#report-container").removeClass("d-none")
    $("#report-container").removeClass("d-block")
    $("#report-container").addClass("d-block")
  show

# A timer used by some charts to do a timed refresh of the results.
REFRESH_MS = 600000  # milliseconds between timed refreshes
_refresh_timer = setInterval update_results, REFRESH_MS

# Handles actions required when the chart type changes.  Mostly sets
# the visibility of controls.
process_chart_change = ->

    # start by hiding all input controls
  set_visibility(['refresh', 'ctrl_sensor', 'ctrl_avg', 'ctrl_avg_export',
    'ctrl_normalize', 'ctrl_occupied', 'xy_controls', 'time_period_group', 
    'download_many', 'get_embed_link','ctrl_use_rolling_averaging'], false)

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

  # Show the proper sensor selector
  single = $('#select_sensor')
  multi = $('#select_sensor_multi')
  if selected_chart_option.data("multi_sensor") == 1
    sensor_val = single.val()
    single.prop('disabled', true)
    single.hide()
    multi.selectpicker('show')
    multi.prop('disabled', false)
    # use last value from single select as the starting value for the multi-select
    multi.selectpicker('val', [sensor_val]) 
    multi.selectpicker('refresh')
    multi.off().change inputs_changed
    $('#label_sensor').html('Select Sensors to Plot:')
  else
    sensor_val = multi.selectpicker('val')[0]
    multi.prop('disabled', true)
    multi.selectpicker('hide')
    single.show()
    single.prop('disabled', false)
    # transfer over the first selected value from the multi-select
    single.val(sensor_val)
    single.off().change inputs_changed
    $('#label_sensor').html('Select Sensor to Plot:')

  # if this is an XY plot, transfer the sensor value over to
  # the Y sensor selector.
  if $('#select_sensor_y').prop('disabled')  == false
    $('#select_sensor_y').val(sensor_val)

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
      $("#select_sensor_multi").html(data.sensors)
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
      # if there is only one item in the facility groups selector, hide it.
      if document.getElementById("select_group").length > 1
        $('#group_controls').show()
      else
        $('#group_controls').hide()

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
      if params.hasOwnProperty(name) and element.length > 0
        new_value = params[name]
        if element[0].getAttribute("type") == "radio"
          old_value = element.filter(":radio:checked").val()
        else if element[0].getAttribute("type") == "checkbox"
          old_value = "needs update"
        else
          old_value = element.val()
        if `old_value != new_value`
          if element[0].getAttribute("type") == "radio"
            # need to use an array to set value of radio buttons.
            element.val([new_value])
            # if this is the time_period radio group, reset the active class
            if element[0].getAttribute("name") == "time_period"
              # special case due to being a Bootstrap 4 button group.
              # remove active from labels, and add active to selected radio's label.
              element.parent().removeClass("active")
              $('input[name=time_period]:checked').parent().addClass("active")
          else if element[0].getAttribute("type") == "checkbox"
            element.prop('checked', true)
          else if element.hasClass('selectpicker')
            # special case of bootstrap-multiselect
            element.selectpicker('val', new_value)
          else
            element.val(new_value)
      element.change() # trigger the change event
    _loading_inputs = false
    params
  
# Function to show or hide the Custom Date range inputs
setCustomDateVis = () ->
  unless $("input:radio[name=time_period]:checked").val() is "custom"
    $("#custom_dates").hide().find("select, input").prop( "disabled", true )
  else
    $("#custom_dates").show().find("select, input").prop( "disabled", false )

# ---------------------------------------------------------------
# function that runs when the document is ready.
$ ->

  # Related to selecting the range of dates to chart
  $('#start_date').datepicker uiLibrary: 'bootstrap4'
  $('#end_date').datepicker uiLibrary: 'bootstrap4'

  d = new Date() # current date to use for a default for Start Date
  $("#start_date").val (d.getMonth() + 1) + "/" + d.getDate() + "/" + d.getFullYear()
  
  # Show and Hide custom date range selector
  $(document).on 'change', 'input:radio[name="time_period"]', setCustomDateVis
  setCustomDateVis()
  
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
  ctrls = ['averaging_time', 'averaging_time_export', 'normalize', 'use_rolling_averaging', 'show_occupied', 
    'select_sensor', 'select_sensor_x', 'select_sensor_y', 'averaging_time_xy', 'div_date',
    'start_date', 'end_date']
  $("##{ctrl}").change inputs_changed for ctrl in ctrls

  # Special change handling of the time period radio inputs.
  $(document).on 'change', 'input:radio[name="time_period"]', inputs_changed

  # Handle any query parameters on the url
  handleUrlQuery()
  
  # Update the window's url to reflect the current inputs state
  history.replaceState(null,null,"?".concat(serializedInputs()))
  
  # Update the display based on the inputs
  inputs_changed()