'''
Holds the base configuration options for Highcharts and Highstock charts.
The options are in YAML format and then converted to a Python dictionary.
Set Tab to 2 spaces.
'''
import yaml

# ------------------------------------ For HighChart ---------------------------------
highcharts_opt = yaml.load(
'''
colors: ["#2f7ed8", "#0d233a", "#8bbc21", "#910000", "#1aadce", "#492970", "#f28f43",
  "#77a1e5", "#c42525", "#a6c96a"]

chart:
  renderTo: chart_container
  spacingTop: 20
  animation: false       # controls animation on redraws, not initial draw
  zoomType: xy
  backgroundColor: "#EEEEEE"
  borderWidth: 2
  plotBackgroundColor: "#FFFFFF"
  plotBorderWidth: 1
  type: line

title:
  style:
    fontSize: 24px

subtitle:
  style:
    fontSize: 22px
  y: 40

tooltip:
  dateTimeLabelFormats:
    millisecond: "%A, %b %e, %H:%M:%S"
    second: "%A, %b %e, %H:%M:%S"
    minute: "%A, %b %e, %H:%M:%S"
    hour: "%A, %b %e, %H:%M:%S"
    day: "%A, %b %e, %H:%M:%S"
    week: "%A, %b %e, %H:%M:%S"
    month: "%A, %b %e, %H:%M:%S"
    year: "%A, %b %e, %H:%M:%S"

yAxis:
  title:
    style:
      fontSize: 16px
  labels:
    style:
      fontSize: 14px

xAxis:
  title:
    style:
      fontSize: 16px

plotOptions:
  series:
    marker:
      enabled: false
      states:
        hover:
          enabled: true

exporting:
  sourceWidth: 930
  sourceHeight: 550
  scale: 1

credits:
  enabled: false

legend:
  enabled: true
  borderWidth: 1
''')

# ------------------------------------ For HighStock ---------------------------------
highstock_opt = yaml.load('''
colors: ["#2f7ed8", "#0d233a", "#8bbc21", "#910000", "#1aadce", "#492970", "#f28f43",
  "#77a1e5", "#c42525", "#a6c96a"]

chart:
  renderTo: "chart_container"
  animation: false
  backgroundColor: "#EEEEEE"
  borderWidth: 2
  plotBackgroundColor: "#FFFFFF"
  plotBorderWidth: 1
  type: "line"
  zoomType: "xy"

title:
  style:
    fontSize: "24px"

xAxis:
  title:
    text: "Date/Time (your computer's time zone)"

  type: "datetime"

tooltip:
  dateTimeLabelFormats:
    millisecond: "%A, %b %e, %H:%M:%S"
    second: "%A, %b %e, %H:%M:%S"
    minute: "%A, %b %e, %H:%M:%S"
    hour: "%A, %b %e, %H:%M:%S"
    day: "%A, %b %e, %H:%M:%S"
    week: "%A, %b %e, %H:%M:%S"
    month: "%A, %b %e, %H:%M:%S"
    year: "%A, %b %e, %H:%M:%S"

  crosshairs: false

xAxis:
  title:
    style:
      fontSize: "16px"

exporting:
  sourceWidth: 930
  sourceHeight: 550
  scale: 1

credits:
  enabled: false

legend:
  enabled: true
  borderWidth: 1  
''')