# A global object variable to attach public methods to 
window.ANdash = {}

# Light red color used to signify value out of normal range.
LIGHT_RED = '#FCC7C7'

# Adds a sparkline gauge control under the container identified by 'jqParent', a jQuery element.
# 'gauge' is an object containing the configuration and value info for the gauge.
# Returns the jQuery div element holding the gauge.
addSparkline = (jqParent, g_info) ->
  xvals = g_info.times
  yvals = g_info.values

  if g_info.unitMeasureType == 'state'
    line_shape = 'hv'
  else
    line_shape = 'linear'
  
  if g_info.value_is_normal
    value_color = 'black'
  else
    value_color = 'red'
    
  data = [
    x: xvals
    y: yvals
    text: g_info.labels
    type: 'scatter'
    mode: 'lines'
    line: {shape: line_shape}
    hoverinfo: 'text'
   ,
    x: xvals.slice(-1)
    y: yvals.slice(-1)
    type: 'scatter'
    mode: 'markers'
    hoverinfo: 'skip'
    marker:
      size: 8
      color: value_color          
  ]
  
  for alert in g_info.alerts
    alert_level =
        x: [g_info.minTime, g_info.maxTime]
        y: [alert.value, alert.value]
        text: ['Alert if value ' + alert.condition + ' ' + alert.value + ' ' + g_info.units]
        type: 'scatter'
        mode: 'markers+lines'
        marker:
            size: 2
            color: 'black'
        line:
            color: 'red'
            width: 0.5
            dash: 'dot'
        hoverinfo: 'text'
     data.push alert_level
    
  plotbands = [
    type: 'rect'
    layer: 'below'
    xref: 'paper'
    yref: 'y'
    fillcolor: 'green'
    opacity: 0.15
    line: {'width': 0}
    x0: 0,
    y0: g_info.minNormal,
    x1: 1,
    y1: g_info.maxNormal
   ]
  
  layout = 
    title: '<b>' + g_info.title + '</b>'
    titlefont:
      color: 'black'
    xaxis:
      range: [g_info.minTime, g_info.maxTime]
      fixedrange: true
      showgrid: false
      zeroline: false
      showline: false
      ticks: ''
      showticklabels: false
    yaxis:
      range: [g_info.minAxis - (g_info.maxAxis - g_info.minAxis) / 20, g_info.maxAxis + (g_info.maxAxis - g_info.minAxis) / 20]
      fixedrange: true
      showgrid: false
      zeroline: false
      ticks: 'outside'
      side: 'left'
    showlegend: false
    margin:
      l: 35
      r: 5
      b: 25
      t: 40
      pad: 0
    shapes: plotbands
    annotations: [
      xref: 'paper'
      yref: 'paper'
      x: 1
      xanchor: 'right'
      y: 0
      yanchor: 'top'
      text: '<b>' + g_info.value_label + '</b>'
      font:
        color: value_color
      showarrow: false
     ]

  
  config =
    showLink: false
    displaylogo: false
    scrollZoom: true
    displayModeBar: false
      
  # Add the div with id that will hold this gauge.
  widgetID = "widget#{++widgetCounter}"    # this increments the counter as well
  jqParent.append( "<div id=\"#{widgetID}\" class=\"gauge\"></div>" )
  jqWidget = $("##{widgetID}")
  jqWidget.css('cursor', 'pointer')   # makes the click hand appear when hovering
  jqWidget.click((e) -> AN.plot_sensor(g_info.timeChartID, g_info.sensorID))
  Plotly.newPlot(jqWidget[0], data, layout, config)
  
  jqWidget        # return the jQuery element holding the gauge
  
  
# Adds an LED widget to dashboard row identified by jQuery elemernt 'jqParent'.
# Info for making LED is in object LED_info.  Returns jQuery div element holding
# LED.
addLED = (jqParent, LED_info) ->
  # Add the div with id that will hold this LED.
  widgetID = "widget#{++widgetCounter}"    # this increments the counter as well
  jqParent.append "<div id=\"#{widgetID}\" class=\"led\">
                     <h2>#{LED_info.title}</h2>
                     <div class=\"led-circle\"></div>
                     <div class=\"value-label\">#{LED_info.value_label}</div>
                   </div>"
  jqWidget = $("##{widgetID}")   # make a jQuery element
  
  # change the color of the LED if needed and the background color of whole div
  if LED_info.value < LED_info.minNormal or LED_info.value > LED_info.maxNormal
    jqWidget.children(".led-circle").css('background-color', '#FF0000')
    jqWidget.css('background-color', LIGHT_RED)

  # add click link
  jqWidget.css('cursor', 'pointer')   # makes the click hand appear when hovering
  jqWidget.click ->
    AN.plot_sensor(LED_info.timeChartID, LED_info.sensorID)
  jqWidget        # return the jQuery element holding the LED
  
# Adds a clickable Label that indicates data is not current. Used in place of a widget
# that displays a sensor value.
addNotCurrent = (jqParent, widget_info) ->
  # Add the div with id that will hold this LED.
  widgetID = "widget#{++widgetCounter}"    # this increments the counter as well
  jqParent.append "<div id=\"#{widgetID}\" class=\"not-current\">
                     <h2>#{widget_info.title}</h2>
                     <h2><i>Data is #{widget_info.age}</i></h2>
                   </div>"
  jqWidget = $("##{widgetID}")   # make a jQuery element
  
  # change the color of the background to indicate problem
  jqWidget.css('background-color', LIGHT_RED)

  # add click link
  jqWidget.css('cursor', 'pointer')   # makes the click hand appear when hovering
  jqWidget.click ->
    AN.plot_sensor(widget_info.timeChartID, widget_info.sensorID)
  jqWidget        # return the jQuery element holding the LED
  
# A Label widget
addLabel = (jqParent, widget_info) ->
  # Add the div with id that will hold this Label
  widgetID = "widget#{++widgetCounter}"    # this increments the counter as well
  jqParent.append "<div id=\"#{widgetID}\" class=\"dash-label\">
                     <h2>#{widget_info.title}</h2>
                   </div>"
  jqWidget = $("##{widgetID}")   # make and return a jQuery element
  

# Variables to track the index of the current row and widget being created
widgetCounter = 0
rowCounter = 0

# Adds one widget to a row in the dashboard.  Returns the jQuery div holding the
# widget.
addWidget = (jqRow, widget_info) ->
  switch widget_info.type
    when "gauge" then addSparkline(jqRow, widget_info)
    when "LED" then addLED(jqRow, widget_info)
    when "stale" then addNotCurrent(jqRow, widget_info)
    when "label" then addLabel(jqRow, widget_info)

# Adds a row of widgets to the dashboard under the div container "jqParent",
# a jQuery element. 'widgetRow' is an array of widget information objects 
# for the row.  Returns the jQuery row div.
addRow = (jqParent, widgetRow) ->
  rowID = "row#{++rowCounter}"     # the css id for the row
  jqParent.append( "<div id=\"#{rowID}\" class=\"row\"></div>" )
  totalWidth = 0
  jqRow = $("##{rowID}")   # a jQuery element for the new row
  totalWidth += addWidget(jqRow, widget_info).width() for widget_info in widgetRow
  # jqRow.width totalWidth     # set the row width = total of widget widths

# Public method for library.  Used to create an entire dashboard.
# "dashConfig.widgets" contains the information for each widget, organized
#  as a list of rows, each row being a list of widget information objects.
# The dashboard is rendered to the div identified by 'dashConfig.renderTo'.
ANdash.createDashboard = (dashConfig) ->
  jqMain = $("##{dashConfig.renderTo}")   # jQuery element of div holding Dashboard
  jqMain.empty()
  addRow jqMain, row for row in dashConfig.widgets
  null  # return nothing
