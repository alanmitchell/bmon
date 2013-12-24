# A global object variable to attach public methods to 
window.ANdash = {}

# Adds a gauge control under the container identified by 'parentID'.
# 'gauge' is an object containing the configuration and value info for the gauge.
# Returns the width of the gauge in pixels.
addGauge = (parentID, gauge) ->

  # Determine parameters that affect how far below the normal range the
  # gauge will extend.
  span = gauge.maxNormal - gauge.minNormal
  scale = if gauge.prePostScale? then gauge.prePostScale else 0.75

  # minVal and maxVal are the extent of the gauge value range.
  # Have to extend gauge range if value is outside bounds, or meter will wrap around.
  minVal = Math.min(gauge.minNormal - span * scale, gauge.value)
  maxVal = Math.max(gauge.maxNormal + span * scale, gauge.value)

  opt =
    chart:
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
      text: gauge.title
      style:
        fontSize: "14px"

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
      min: minVal
      max: maxVal
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
        text: gauge.units

      plotBands: [
        from: minVal
        to: gauge.minNormal
        color: "#DF5353"  # red
       ,
        from: gauge.minNormal
        to: gauge.maxNormal
        color: "#55BF3B" # green
       ,
        from: gauge.maxNormal
        to: maxVal
        color: "#DF5353"  # red
      ]

    series: [
      data: [gauge.value]
      tooltip:
        valueSuffix: " #{gauge.units}"
    ]

  # turn the background light red if the value is abnormal.
  opt.chart.backgroundColor = "#FCC7C7" if not (gauge.minNormal <= gauge.value <= gauge.maxNormal)

  # Add the div with id that will hold this gauge.
  widgetID = "widget#{widgetCounter++}"    # this increments the counter as well
  $("##{parentID}").append( "<div id=\"#{widgetID}\" class=\"gauge\"></div>" )
  $("##{widgetID}").highcharts(opt).width()  # return the width of the gauge


# Variables to track the index of the current row and widget being created
widgetCounter = 0
rowCounter = 0

# Adds a row of widgets to the dashboard under container 'parentID'.
# 'widgetRow' is an array of widgets for the row.
addRow = (parentID, widgetRow) ->
  rowID = "row#{rowCounter++}"
  $("##{parentID}").append( "<div id=\"#{rowID}\" class=\"row\"></div>" )
  totalWidth = 0
  totalWidth += addGauge(rowID, widget) for widget in widgetRow
  $("##{rowID}").width totalWidth


ANdash.createDashboard = (parentID, dashConfig) ->
  $("##{parentID}").empty()
  addRow parentID, row for row in dashConfig.widgets
