(function() {
  var LIGHT_RED, addLED, addLabel, addNotCurrent, addRow, addSparkline, addWidget, rowCounter, widgetCounter;

  window.ANdash = {};

  LIGHT_RED = '#FCC7C7';

  addSparkline = function(jqParent, g_info) {
    var alert, alert_level, config, data, i, jqWidget, layout, len, line_shape, plotbands, ref, value_color, widgetID, xvals, yvals;
    xvals = g_info.times;
    yvals = g_info.values;
    if (g_info.unitMeasureType === 'state') {
      line_shape = 'hv';
    } else {
      line_shape = 'linear';
    }
    if (g_info.value_is_normal) {
      value_color = 'black';
    } else {
      value_color = 'red';
    }
    data = [
      {
        x: xvals,
        y: yvals,
        text: g_info.labels,
        type: 'scatter',
        mode: 'lines',
        line: {
          shape: line_shape
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
          color: value_color
        }
      }
    ];
    ref = g_info.alerts;
    for (i = 0, len = ref.length; i < len; i++) {
      alert = ref[i];
      alert_level = {
        x: [g_info.minTime, g_info.maxTime],
        y: [alert.value, alert.value],
        text: ['Alert if value ' + alert.condition + ' ' + alert.value + ' ' + g_info.units],
        type: 'scatter',
        mode: 'markers+lines',
        marker: {
          size: 2,
          color: 'black'
        },
        line: {
          color: 'red',
          width: 0.5,
          dash: 'dot'
        },
        hoverinfo: 'text'
      };
      data.push(alert_level);
    }
    plotbands = [
      {
        type: 'rect',
        layer: 'below',
        xref: 'paper',
        yref: 'y',
        fillcolor: 'green',
        opacity: 0.15,
        line: {
          'width': 0
        },
        x0: 0,
        y0: g_info.minNormal,
        x1: 1,
        y1: g_info.maxNormal
      }
    ];
    layout = {
      title: '<b>' + g_info.title + '</b>',
      titlefont: {
        color: 'black',
        size: 14
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
      annotations: [
        {
          xref: 'paper',
          yref: 'paper',
          x: 1,
          xanchor: 'right',
          y: 0,
          yanchor: 'top',
          text: '<b>' + g_info.value_label + '</b>',
          font: {
            color: value_color
          },
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
    if (!LED_info.value_is_normal) {
      jqWidget.children(".led-circle").css('background-color', '#FF0000');
      jqWidget.children(".value-label").css('color', '#FF0000');
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
