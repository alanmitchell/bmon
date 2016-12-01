(function() {
  var LIGHT_RED, addGauge, addLED, addLabel, addNotCurrent, addRow, addSparkline, addWidget, rowCounter, widgetCounter;

  window.ANdash = {};

  LIGHT_RED = '#FCC7C7';

  addGauge = function(jqParent, g_info) {
    var jqWidget, opt, ref, widgetID;
    opt = {
      chart: {
        events: {
          click: null
        },
        type: "gauge",
        backgroundColor: 'rgba(255, 255, 255, 0.1)',
        plotBackgroundColor: null,
        plotBackgroundImage: null,
        plotBorderWidth: 0,
        plotShadow: false
      },
      credits: {
        enabled: false
      },
      exporting: {
        enabled: false
      },
      title: {
        text: g_info.title,
        style: {
          fontSize: "13px"
        }
      },
      pane: {
        startAngle: -130,
        endAngle: 130,
        background: [
          {
            backgroundColor: {
              linearGradient: {
                x1: 0,
                y1: 0,
                x2: 0,
                y2: 1
              },
              stops: [[0, "#FFF"], [1, "#333"]]
            },
            borderWidth: 0,
            outerRadius: "109%"
          }, {
            backgroundColor: {
              linearGradient: {
                x1: 0,
                y1: 0,
                x2: 0,
                y2: 1
              },
              stops: [[0, "#333"], [1, "#FFF"]]
            },
            borderWidth: 1,
            outerRadius: "107%"
          }, {}, {
            backgroundColor: "#DDD",
            borderWidth: 0,
            outerRadius: "105%",
            innerRadius: "103%"
          }
        ]
      },
      plotOptions: {
        series: {
          dataLabels: {
            style: {
              fontSize: "14px"
            }
          }
        }
      },
      yAxis: {
        min: g_info.minAxis,
        max: g_info.maxAxis,
        minorTickInterval: "auto",
        minorTickWidth: 1,
        minorTickLength: 10,
        minorTickPosition: "inside",
        minorTickColor: "#666",
        tickPixelInterval: 30,
        tickWidth: 2,
        tickPosition: "inside",
        tickLength: 10,
        tickColor: "#666",
        labels: {
          step: 2,
          rotation: "auto",
          style: {
            fontSize: "10px"
          }
        },
        title: {
          text: g_info.units
        },
        plotBands: [
          {
            from: g_info.minAxis,
            to: g_info.minNormal,
            color: "#DF5353"
          }, {
            from: g_info.minNormal,
            to: g_info.maxNormal,
            color: "#55BF3B"
          }, {
            from: g_info.maxNormal,
            to: g_info.maxAxis,
            color: "#DF5353"
          }
        ]
      },
      series: [
        {
          data: [g_info.value],
          tooltip: {
            valueSuffix: " " + g_info.units
          }
        }
      ]
    };
    if (!((g_info.minNormal <= (ref = g_info.value) && ref <= g_info.maxNormal))) {
      opt.chart.backgroundColor = LIGHT_RED;
    }
    widgetID = "widget" + (++widgetCounter);
    jqParent.append("<div id=\"" + widgetID + "\" class=\"gauge\"></div>");
    jqWidget = $("#" + widgetID);
    jqWidget.css('cursor', 'pointer');
    opt.chart.events.click = function(e) {
      return AN.plot_sensor(g_info.timeChartID, g_info.sensorID);
    };
    return jqWidget.highcharts(opt);
  };

  addSparkline = function(jqParent, g_info) {
    var config, data, jqWidget, layout, plotbands, widgetID, xvals, yvals;
    xvals = g_info.times;
    yvals = g_info.values;
    plotbands = [
      {
        type: 'rect',
        layer: 'below',
        xref: 'paper',
        yref: 'y',
        fillcolor: 'red',
        opacity: 0.6,
        line: {
          'width': 0
        },
        x0: 0,
        y0: g_info.minAxis,
        x1: 1,
        y1: g_info.minNormal
      }, {
        type: 'rect',
        layer: 'below',
        xref: 'paper',
        yref: 'y',
        fillcolor: 'red',
        opacity: 0.6,
        line: {
          'width': 0
        },
        x0: 0,
        y0: g_info.maxNormal,
        x1: 1,
        y1: g_info.maxAxis
      }
    ];
    data = [
      {
        x: xvals,
        y: yvals,
        type: 'scatter',
        mode: 'lines',
        hoverinfo: 'x+y'
      }, {
        x: xvals.slice(-1),
        y: yvals.slice(-1),
        type: 'scatter',
        mode: 'markers',
        hoverinfo: 'skip',
        marker: {
          size: 8,
          color: 'rgba(0, 0, 0, 0.7)'
        }
      }
    ];
    layout = {
      title: g_info.title,
      titlefont: {
        color: 'black'
      },
      xaxis: {
        range: [g_info.minTime, g_info.maxTime],
        fixedrange: true,
        showgrid: false,
        zeroline: false,
        showline: false,
        ticks: '',
        showticklabels: false
      },
      yaxis: {
        range: [g_info.minAxis, g_info.maxAxis],
        fixedrange: true,
        showgrid: false,
        zeroline: false,
        ticks: 'outside',
        side: 'left'
      },
      showlegend: false,
      hovermode: 'closest',
      margin: {
        l: 30,
        r: 5,
        b: 30,
        t: 40,
        pad: 0
      },
      shapes: plotbands,
      annotations: [
        {
          xref: 'paper',
          yref: 'paper',
          x: 1,
          xanchor: 'right',
          y: 0,
          yanchor: 'top',
          text: '<b>' + g_info.value_label + ' ' + g_info.units + '</b>',
          showarrow: false
        }
      ]
    };
    config = {
      showLink: false,
      displaylogo: false,
      scrollZoom: true,
      displayModeBar: false
    };
    widgetID = "widget" + (++widgetCounter);
    jqParent.append("<div id=\"" + widgetID + "\" class=\"gauge\"></div>");
    jqWidget = $("#" + widgetID);
    jqWidget.css('cursor', 'pointer');
    jqWidget.click(function(e) {
      return AN.plot_sensor(g_info.timeChartID, g_info.sensorID);
    });
    Plotly.newPlot(jqWidget[0], data, layout, config);
    return jqWidget;
  };

  addLED = function(jqParent, LED_info) {
    var jqWidget, widgetID;
    widgetID = "widget" + (++widgetCounter);
    jqParent.append("<div id=\"" + widgetID + "\" class=\"led\"> <h2>" + LED_info.title + "</h2> <div class=\"led-circle\"></div> <div class=\"value-label\">" + LED_info.value_label + "</div> </div>");
    jqWidget = $("#" + widgetID);
    if (LED_info.value < LED_info.minNormal || LED_info.value > LED_info.maxNormal) {
      jqWidget.children(".led-circle").css('background-color', '#FF0000');
      jqWidget.css('background-color', LIGHT_RED);
    }
    jqWidget.css('cursor', 'pointer');
    jqWidget.click(function() {
      return AN.plot_sensor(LED_info.timeChartID, LED_info.sensorID);
    });
    return jqWidget;
  };

  addNotCurrent = function(jqParent, widget_info) {
    var jqWidget, widgetID;
    widgetID = "widget" + (++widgetCounter);
    jqParent.append("<div id=\"" + widgetID + "\" class=\"not-current\"> <h2>" + widget_info.title + "</h2> <h2><i>Data is " + widget_info.age + "</i></h2> </div>");
    jqWidget = $("#" + widgetID);
    jqWidget.css('background-color', LIGHT_RED);
    jqWidget.css('cursor', 'pointer');
    jqWidget.click(function() {
      return AN.plot_sensor(widget_info.timeChartID, widget_info.sensorID);
    });
    return jqWidget;
  };

  addLabel = function(jqParent, widget_info) {
    var jqWidget, widgetID;
    widgetID = "widget" + (++widgetCounter);
    jqParent.append("<div id=\"" + widgetID + "\" class=\"dash-label\"> <h2>" + widget_info.title + "</h2> </div>");
    return jqWidget = $("#" + widgetID);
  };

  widgetCounter = 0;

  rowCounter = 0;

  addWidget = function(jqRow, widget_info) {
    switch (widget_info.type) {
      case "gauge":
        return addSparkline(jqRow, widget_info);
      case "LED":
        return addLED(jqRow, widget_info);
      case "stale":
        return addNotCurrent(jqRow, widget_info);
      case "label":
        return addLabel(jqRow, widget_info);
    }
  };

  addRow = function(jqParent, widgetRow) {
    var i, jqRow, len, results, rowID, totalWidth, widget_info;
    rowID = "row" + (++rowCounter);
    jqParent.append("<div id=\"" + rowID + "\" class=\"row\"></div>");
    totalWidth = 0;
    jqRow = $("#" + rowID);
    results = [];
    for (i = 0, len = widgetRow.length; i < len; i++) {
      widget_info = widgetRow[i];
      results.push(totalWidth += addWidget(jqRow, widget_info).width());
    }
    return results;
  };

  ANdash.createDashboard = function(dashConfig) {
    var i, jqMain, len, ref, row;
    jqMain = $("#" + dashConfig.renderTo);
    jqMain.empty();
    ref = dashConfig.widgets;
    for (i = 0, len = ref.length; i < len; i++) {
      row = ref[i];
      addRow(jqMain, row);
    }
    return null;
  };

}).call(this);

//# sourceMappingURL=dashboard.js.map
