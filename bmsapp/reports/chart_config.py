'''
Holds the base configuration options for charts.
The options are in YAML format and then converted to a Python dictionary.
Set Tab to 2 spaces.
'''
import yaml

# ------------------------------------ For Plotly Chart -----------------------------
plotly_opt = yaml.load(
'''
data: []    # Trace data is programmatically added here

layout:
  titlefont:
    family: Arial, monospace
    size: 40
    color: black
  xaxis:
    title: Date/Time
    titlefont:
      family: Arial, monospace
      size: 18
      color: black
  yaxis:
    title: Value
    titlefont:
      family: Arial, monospace
      size: 18
      color: black

config:
  showLink: false
  displaylogo: false
  scrollZoom: true
''')

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
    color: black

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

xAxis:
  title:
    style:
      fontSize: 16px
      color: black
  labels:
    style:
      fontSize: 14px
      color: black

yAxis:
  title:
    style:
      fontSize: 16px
      color: black
  labels:
    style:
      fontSize: 15px
      color: black

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
  scale: 1.5

credits:
  enabled: false

legend:
  enabled: true
  borderWidth: 1
''')

# ------------------------------------ For Heat Map Charts ---------------------------------
heatmap_opt = yaml.load('''
chart:
  renderTo: chart_container
  type: heatmap
  height: 400
  marginTop: 40
  marginBottom: 40
  backgroundColor: "#EEEEEE"
  plotBorderWidth: 1

title:
  style:
    fontSize: 24px
    color: black

xAxis:
  labels:
    style:
      fontSize: 13px
      color: black

yAxis:
  labels:
    style:
      fontSize: 14px
      color: black

colorAxis:
  minColor: "#FFFFFF"
  maxColor: "#0066FF"

tooltip:
  pointFormat: "<b>{point.value}</b>"

legend:
  align: right
  layout: vertical
  margin: 0
  verticalAlign: top
  y: 40
  symbolHeight: 280

exporting:
  sourceWidth: 930
  sourceHeight: 400
  scale: 1.5

credits:
  enabled: false
''')

# ------------------------------------ For HighStock ---------------------------------
highstock_opt = yaml.load('''
colors: ["#2f7ed8", "#0d233a", "#8bbc21", "#910000", "#1aadce", "#492970", "#f28f43",
  "#77a1e5", "#c42525", "#a6c96a"]

chart:
  renderTo: chart_container
  animation: false
  backgroundColor: "#EEEEEE"
  borderWidth: 2
  plotBackgroundColor: "#FFFFFF"
  plotBorderWidth: 1
  type: line
  zoomType: xy

title:
  style:
    fontSize: 24px
    color: black

xAxis:
  ordinal: false
  title:
    text: Date/Time (your computer's time zone)
    style:
      fontSize: 16px
      color: black
  labels:
    style:
      fontSize: 14px
      color: black

yAxis:
  title:
    style:
      fontSize: 16px
      color: black
  labels:
    style:
      fontSize: 14px
      color: black

navigator:
  margin: 0

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

exporting:
  sourceWidth: 930
  sourceHeight: 550
  scale: 1.5

credits:
  enabled: false

legend:
  enabled: true
  borderWidth: 1  
''')