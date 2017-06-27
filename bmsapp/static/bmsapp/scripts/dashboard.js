(function() {
  var LIGHT_RED, addGauge, addLED, addLabel, addNotCurrent, addRow, addSparkline, addWidget, rowCounter, widgetCounter;

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
        text: ['Alert if value' + ' ' + alert.condition + ' ' + alert.value + ' ' + g_info.units],
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
      title: '',
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
        b: 5,
        t: 10,
        pad: 0
      },
      shapes: plotbands
    };
    config = {
      showLink: false,
      displaylogo: false,
      scrollZoom: true,
      displayModeBar: false
    };
    widgetID = "widget" + (++widgetCounter);
    jqParent.append("<div id=\"" + widgetID + "\" class=\"dash-widget\"> <div class=\"widget-title\">" + g_info.title + "</div> <div class=\"graph\"></div> <div class=\"value-label\">" + g_info.value_label + "</div> </div>");
    jqWidget = $("#" + widgetID);
    jqWidget.css('cursor', 'pointer');
    jqWidget.click(function() {
      return window.location = g_info.href;
    });
    if (!g_info.value_is_normal) {
      jqWidget.children(".value-label").css('color', '#FF0000');
    }
    Plotly.newPlot(jqWidget[0].children[1], data, layout, config);
    return jqWidget;
  };

  addGauge = function(jqParent, g_info) {
    var gauge, gauge_normal_color, gauge_zone_color, jqWidget, opts, widgetID;
    widgetID = "widget" + (++widgetCounter);
    jqParent.append("<div id=\"" + widgetID + "\" class=\"dash-widget\"> <div class=\"widget-title\">" + g_info.title + "</div> <canvas class=\"gauge-canvas\"></canvas> <div class=\"value-label\">" + g_info.value_label + "</div> </div>");
    jqWidget = $("#" + widgetID);
    jqWidget.css('cursor', 'pointer');
    jqWidget.click(function() {
      return window.location = g_info.href;
    });
    if (g_info.value_is_normal) {
      gauge_zone_color = "#E0E0E0";
      gauge_normal_color = "#BFDFBF";
    } else {
      jqWidget.children(".value-label").css('color', '#FF0000');
      gauge_zone_color = "red";
      gauge_normal_color = "#BFDFBF";
    }
    opts = {
      angle: -0.1,
      radiusScale: 0.85,
      pointer: {
        length: 0.6
      },
      staticLabels: {
        font: "12px 'Open Sans', verdana, arial, sans-serif",
        labels: [g_info.minAxis, g_info.minNormal, g_info.maxNormal, g_info.maxAxis],
        color: "#000000",
        fractionDigits: 0
      },
      staticZones: [
        {
          strokeStyle: gauge_zone_color,
          min: g_info.minAxis,
          max: g_info.minNormal
        }, {
          strokeStyle: gauge_normal_color,
          min: g_info.minNormal,
          max: g_info.maxNormal
        }, {
          strokeStyle: gauge_zone_color,
          min: g_info.maxNormal,
          max: g_info.maxAxis
        }
      ]
    };
    gauge = new Gauge(jqWidget[0].children[1]).setOptions(opts);
    gauge.maxValue = g_info.maxAxis;
    gauge.setMinValue(g_info.minAxis);
    gauge.set(g_info.values.slice(-1));
    return jqWidget;
  };

  addLED = function(jqParent, LED_info) {
    var jqWidget, widgetID;
    widgetID = "widget" + (++widgetCounter);
    jqParent.append("<div id=\"" + widgetID + "\" class=\"dash-widget\"> <div class=\"widget-title\">" + LED_info.title + "</div> <div class=\"led-circle\"></div> <div class=\"value-label\">" + LED_info.value_label + "</div> </div>");
    jqWidget = $("#" + widgetID);
    if (!LED_info.value_is_normal) {
      jqWidget.children(".led-circle").css('background-color', '#FF0000');
      jqWidget.children(".value-label").css('color', '#FF0000');
    }
    jqWidget.css('cursor', 'pointer');
    jqWidget.click(function() {
      return window.location = LED_info.href;
    });
    return jqWidget;
  };

  addNotCurrent = function(jqParent, widget_info) {
    var jqWidget, widgetID;
    widgetID = "widget" + (++widgetCounter);
    jqParent.append("<div id=\"" + widgetID + "\" class=\"dash-widget\"> <div class=\"widget-title\">" + widget_info.title + "</div> <h2><i>Data is " + widget_info.age + "</i></h2> </div>");
    jqWidget = $("#" + widgetID);
    jqWidget.css('background-color', LIGHT_RED);
    jqWidget.css('cursor', 'pointer');
    jqWidget.click(function() {
      return window.location = widget_info.href;
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
      case "graph":
        return addSparkline(jqRow, widget_info);
      case "gauge":
        return addGauge(jqRow, widget_info);
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

  ANdash.createDashboard = function(dashConfig, renderTo) {
    var i, jqMain, len, ref, row;
    if (renderTo != null) {
      jqMain = $(renderTo);
    } else {
      jqMain = $("#" + dashConfig.renderTo);
    }
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
