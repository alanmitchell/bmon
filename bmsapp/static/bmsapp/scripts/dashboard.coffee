# A global object variable to attach public methods to 
window.ANdash = {}

# Light red color used to signify value out of normal range.
LIGHT_RED = '#FCC7C7'

# Adds a gauge control under the container identified by 'jqParent', a jQuery element.
# 'gauge' is an object containing the configuration and value info for the gauge.
# Returns the jQuery div element holding the gauge.
addGauge = (jqParent, g_info) ->

  opt =
    chart:
      events:
        click: null
      type: "gauge"
      backgroundColor: 'rgba(255, 255, 255, 0.1)'
      plotBackgroundColor: null
      plotBackgroundImage: null
      plotBorderWidth: 0
      plotShadow: false

    credits:
      enabled: false

    exporting:
      enabled: false

    title:
      text: g_info.title
      style:
        fontSize: "13px"

    pane:
      startAngle: -130
      endAngle: 130
      background: [
        backgroundColor:
          linearGradient:
            x1: 0
            y1: 0
            x2: 0
            y2: 1

          stops: [[0, "#FFF"], [1, "#333"]]

        borderWidth: 0
        outerRadius: "109%"
      ,
        backgroundColor:
          linearGradient:
            x1: 0
            y1: 0
            x2: 0
            y2: 1

          stops: [[0, "#333"], [1, "#FFF"]]

        borderWidth: 1
        outerRadius: "107%"
      , {},
        # default background
        backgroundColor: "#DDD"
        borderWidth: 0
        outerRadius: "105%"
        innerRadius: "103%"
      ]

    plotOptions:
      series:
        dataLabels:
          style:
            fontSize: "14px"

    # the value axis
    yAxis:
      min: g_info.minAxis
      max: g_info.maxAxis
      minorTickInterval: "auto"
      minorTickWidth: 1
      minorTickLength: 10
      minorTickPosition: "inside"
      minorTickColor: "#666"
      tickPixelInterval: 30
      tickWidth: 2
      tickPosition: "inside"
      tickLength: 10
      tickColor: "#666"
      labels:
        step: 2
        rotation: "auto"
        style:
          fontSize: "10px"

      title:
        text: g_info.units

      plotBands: [
        from: g_info.minAxis
        to: g_info.minNormal
        color: "#DF5353"  # red
       ,
        from: g_info.minNormal
        to: g_info.maxNormal
        color: "#55BF3B" # green
       ,
        from: g_info.maxNormal
        to: g_info.maxAxis
        color: "#DF5353"  # red
      ]

    series: [
      data: [g_info.value]
      tooltip:
        valueSuffix: " #{g_info.units}"
    ]

  # turn the background light red if the value is abnormal.
  opt.chart.backgroundColor = LIGHT_RED if not (g_info.minNormal <= g_info.value <= g_info.maxNormal)

  # Add the div with id that will hold this gauge.
  widgetID = "widget#{++widgetCounter}"    # this increments the counter as well
  jqParent.append( "<div id=\"#{widgetID}\" class=\"gauge\"></div>" )
  jqWidget = $("##{widgetID}")
  jqWidget.css('cursor', 'pointer')   # makes the click hand appear when hovering
  opt.chart.events.click = (e) ->
    AN.plot_sensor(g_info.timeChartID, g_info.sensorID)
  jqWidget.highcharts(opt)        # return the jQuery element holding the gauge


# Adds a sparkline gauge control under the container identified by 'jqParent', a jQuery element.
# 'gauge' is an object containing the configuration and value info for the gauge.
# Returns the jQuery div element holding the gauge.
addSparkline = (jqParent, g_info) ->
  xvals = g_info.times
  yvals = g_info.values
  plotbands = [
    type: 'rect',
    layer: 'below',
    xref: 'paper',
    yref: 'y',
    fillcolor: 'red',
    opacity: 0.6,
    line: {'width': 0},
    x0: 0,
    y0: g_info.minAxis,
    x1: 1,
    y1: g_info.minNormal
   ,
    type: 'rect',
    layer: 'below',
    xref: 'paper',
    yref: 'y',
    fillcolor: 'red',
    opacity: 0.6,
    line: {'width': 0},
    x0: 0,
    y0: g_info.maxNormal,
    x1: 1,
    y1: g_info.maxAxis
   ]
  data = [
    x: xvals
    y: yvals
    type: 'scatter'
    mode: 'lines'
    hoverinfo: 'x+y'
   ,
    x: xvals.slice(-1)
    y: yvals.slice(-1)
    type: 'scatter'
    mode: 'markers'
    hoverinfo: 'skip'
    marker:
      size: 8
      color: 'rgba(0, 0, 0, 0.7)'          
  ]
  
  layout = 
    title: g_info.title
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
      range: [g_info.minAxis, g_info.maxAxis]
      fixedrange: true
      showgrid: false
      zeroline: false
      ticks: 'outside'
      side: 'left'
    showlegend: false
    hovermode: 'closest'
    margin:
      l: 30
      r: 5
      b: 30
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
      text: '<b>' + g_info.value_label + ' ' + g_info.units + '</b>'
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
