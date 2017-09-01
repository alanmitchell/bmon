'''
Holds the base configuration options for charts.
The options are in YAML format and then converted to a Python dictionary.
Set Tab to 2 spaces.
'''
import yaml

# ------------------------------------ For Plotly Chart -----------------------------
plotly_opt = yaml.load(
'''
renderTo: chart_container     # the name of the div to render into

data: []    # Trace data is programmatically added here

layout:
  font:
    family: Open Sans, verdana, arial, sans-serif
    color: black
  paper_bgcolor: '#EEEEEE'
  hovermode: closest
  titlefont:
    size: 22
  autosize: true
  margin:
    l: 65
    r: 20
    b: 10
    t: 75
    pad: 5
  showlegend: true
  legend:
    orientation: h
    xanchor: center
    yanchor: top
    x: 0.5
    y: -0.2
    borderwidth: 1
  xaxis:
    title: Date/Time
    titlefont:
      size: 14
  yaxis:
    title: Value
    titlefont:
      size: 14

config:
  showLink: false
  displaylogo: false
  scrollZoom: true
''')

def chart_container_html(title="Plotly Chart"):
    # Generate a container element and a hidden title
    return '<h2 id="report_title" hidden>{}</h2><div id="chart_container" style="border-style:solid; border-width:2px; border-color:#4572A7; flex-grow:1"></div>'.format(title)
