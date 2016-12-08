(function() {
  var LIGHT_RED, addLED, addLabel, addNotCurrent, addRow, addSparkline, addWidget, rowCounter, widgetCounter,
    slice = [].slice;

  window.ANdash = {};

  LIGHT_RED = '#FCC7C7';

  addSparkline = function(jqParent, g_info) {
    var alert, alert_annotation, alert_labels, config, data, i, jqWidget, layout, len, plotbands, ref, ref1, widgetID, xvals, yvals;
    xvals = g_info.times;
    yvals = g_info.values;
    data = [
      {
        x: xvals,
        y: yvals,
        text: g_info.labels,
        type: 'scatter',
        mode: 'lines',
        line: {
          shape: (ref = g_info.unitMeasureType === 'state') != null ? ref : {
            'hv': 'linear'
          }
        },
        hoverinfo: 'text'
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
    alert_labels = [];
    ref1 = g_info.alerts;
    for (i = 0, len = ref1.length; i < len; i++) {
      alert = ref1[i];
      alert_annotation = {
        xref: 'paper',
        yref: 'y',
        x: 0,
        y: alert.value,
        ax: 25,
        ay: 0,
        xanchor: 'left',
        yanchor: 'middle',
        text: alert.condition,
        font: {
          color: 'black',
          size: 14
        },
        bordercolor: 'red',
        bgcolor: 'white',
        showarrow: true,
        arrowcolor: 'red',
        arrowhead: 7,
        arrowsize: .75
      };
      alert_labels.push(alert_annotation);
    }
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
        range: [g_info.minAxis - (g_info.maxAxis - g_info.minAxis) / 20, g_info.maxAxis + (g_info.maxAxis - g_info.minAxis) / 20],
        fixedrange: true,
        showgrid: false,
        zeroline: false,
        ticks: 'outside',
        side: 'left'
      },
      showlegend: false,
      margin: {
        l: 35,
        r: 5,
        b: 25,
        t: 40,
        pad: 0
      },
      shapes: plotbands,
      annotations: slice.call(alert_labels).concat([{
          xref: 'paper',
          yref: 'paper',
          x: 1,
          xanchor: 'right',
          y: 0,
          yanchor: 'top',
          text: '<b>' + g_info.value_label + ' ' + g_info.units + '</b>',
          showarrow: false
        }])
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
