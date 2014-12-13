
// my object to contain all global variables and functions.  Minimizes
// global namespace pollution.
var AN = {
        chart: null,        // the current chart object
        chart_makers: {}   // holds chart classes
    };                    

// Returns the part of the URL that identifies the chart type (multi-building
// or one building) and the chart ID.
AN.make_chart_id_url = function() {

    // get building selected
    var bldg = $("#select_bldg").val();

    // get chart selected
    var chart = $("#select_chart").val();

    var base = $("#BaseURL").text() + "chart/";

    // create a string to identify the chart: bldg ID + "/" + chart ID for a chart associated
    // with one building. If the chart is associated with multiple
    // buildings, the string is "multi/" + chart ID
    if (bldg=="multi") {
        return base + "multi/" + chart;
    } else {
        return base + bldg + "/" + chart;
    }
}

/*******************************************************************************
* Chart Classes and Helper Functions go here under the AN.chart_classes object *
********************************************************************************/

// Returns basic Highcharts options
AN.chart_makers.cht_options = function() {
    return {
        colors: ['#2f7ed8', '#0d233a', '#8bbc21', '#910000', '#1aadce', '#492970',
            '#f28f43', '#77a1e5', '#c42525', '#a6c96a'],

        chart: {
            renderTo: 'chart_container',
            spacingTop: 20,
            animation: false,    // controls animation on redraws, not initial draw
            zoomType: 'xy',
            backgroundColor: '#EEEEEE',
            borderWidth: 2,
            plotBackgroundColor: '#FFFFFF',
            plotBorderWidth: 1
        },

        title : {
            style: {fontSize: '24px'}
        },
        subtitle : {
            style: {fontSize: '22px'},
            y : 40
        },

        tooltip: {
            dateTimeLabelFormats: {
                millisecond:"%A, %b %e, %H:%M:%S",
                second:"%A, %b %e, %H:%M:%S",
                minute:"%A, %b %e, %H:%M:%S",
                hour:"%A, %b %e, %H:%M:%S",
                day:"%A, %b %e, %H:%M:%S",
                week:"%A, %b %e, %H:%M:%S",
                month:"%A, %b %e, %H:%M:%S",
                year:"%A, %b %e, %H:%M:%S"
            }
        },

        yAxis : {
            title: {
                style: {fontSize: '16px'}
            },
            labels: {
                style: {fontSize: '14px'}
            }
        },

        xAxis: {
            title: {
                style: {fontSize: '16px'}
            }
        },

        plotOptions: {
            series: {
                marker: {
                    enabled: false,
                    states: {
                        hover: {
                            enabled: true
                        }
                    }
                }
            }
        },

        exporting: {
            sourceWidth: 930,
            sourceHeight: 550,
            scale: 1
        },

        credits: {
            enabled: false
        },

        legend : {
            enabled : true,
            borderWidth: 1
        },

        series: [{}]
    };
}
AN.chart_makers.cht_stock_options = function() {
    return {
        colors: ['#2f7ed8', '#0d233a', '#8bbc21', '#910000', '#1aadce', '#492970',
            '#f28f43', '#77a1e5', '#c42525', '#a6c96a'],

        chart: {
            renderTo: 'chart_container',
            animation: false,    // controls animation on redraws, not initial draw
            backgroundColor: '#EEEEEE',
            borderWidth: 2,
            plotBackgroundColor: '#FFFFFF',
            plotBorderWidth: 1,
            type: "line",
            zoomType: 'xy'
        },

        title : {
            style: {fontSize: '24px'}
        },

        xAxis : {
            title: {
                text: "Date/Time (your computer's time zone)"
            },
            type: "datetime"
        },

        tooltip: {
            dateTimeLabelFormats: {
                millisecond:"%A, %b %e, %H:%M:%S",
                second:"%A, %b %e, %H:%M:%S",
                minute:"%A, %b %e, %H:%M:%S",
                hour:"%A, %b %e, %H:%M:%S",
                day:"%A, %b %e, %H:%M:%S",
                week:"%A, %b %e, %H:%M:%S",
                month:"%A, %b %e, %H:%M:%S",
                year:"%A, %b %e, %H:%M:%S"
            },
            crosshairs: false
        },

        xAxis: {
            title: {
                style: {fontSize: '16px'}
            }
        },

        exporting: {
            sourceWidth: 930,
            sourceHeight: 550,
            scale: 1
        },

        credits: {
            enabled: false
        },

        legend : {
            enabled : true,
            borderWidth: 1
        },

    };
}

// Removes all the series on the 'the_chart' Highcharts chart and replaces them 
// with 'new_series'.  If 'only_show_first' is true, hide all series except the first 
// (optional argument).
AN.chart_makers.replace_series = function(the_chart, new_series, only_show_first) {

    // deal with optional 'only_show_first' argument
    only_show_first = (typeof only_show_first === "undefined") ? false : only_show_first;

    while (the_chart.series.length) { the_chart.series[0].remove() }
    $.each(new_series, function(idx, a_series) {
        // keeps colors starting from the beginning
        a_series.color = the_chart.options.colors[idx];  
        the_chart.addSeries(a_series, false);
        if (idx>0 & only_show_first) the_chart.series[idx].hide();   // only show first series initially
    });

}

// Does some common configuration of the chart configuration UI and returns a
// basic chart object that contains properties and 
AN.chart_makers.base_chart = function() {

    // Configure many of the elements that commonly appear in chart configuration
    // form.

    $("#time_period").buttonset();

    // Related to selecting the range of dates to chart
    $( "#start_date" ).datepicker({dateFormat: "mm/dd/yy"});
    var d = new Date();   // current date to use for a default for Start Date
    $( "#start_date" ).val((d.getMonth()+1) + "/" + d.getDate() + "/" + d.getFullYear());
    $( "#end_date" ).datepicker({dateFormat: "mm/dd/yy"});
    $("#custom_dates").hide(0);   // hide custom dates element
    // Show and Hide custom date range selector
    $("#time_period").change(function() {
        if ($('input:radio[name=time_period]:checked').val() != "custom") {
            $("#custom_dates").hide();
        } else {
            $("#custom_dates").show();
        }
    });

    // if the sensor select control is a multi-select, set it up
    if($("#select_sensor[multiple]").length) {
        $("#select_sensor").multiselect( {minWidth: 250} );
    }

    // Force Highcharts to display in the timezone of the Browser instead of UTC.
    // this is a Global Highcharts option, not a chart specific option.
    // Note, would be better to have Highcharts display in the timezone where the data
    // was collected (US/Alaska), but that is not possible through configuration of 
    // Highcharts.
    Highcharts.setOptions({
        global: {
            useUTC: false
        }
    });

    // Retrieve the base set of chart options and customize somewhat
    var ch_opt = AN.chart_makers.cht_options();
    ch_opt.title.text = $("#select_chart option:selected").text() + ": " +
        $("#select_bldg option:selected").text();

    var cht_obj = {
        chart_options: ch_opt,
        data_url: AN.make_chart_id_url() + "/data/",
        redraw: null     // need to override this to configure and draw chart
    };

    // Because this function is used in an event callback, you cannot reference the 
    // object with the "this" keyword, since "this" is set to the DOM element that fired
    // the event.  So, instead, reference the object with the actual "cht_obj" variable
    // which is maintained due to closure.
    // NOTE: there is no "prototype" property for an object literal, so the "get_data" method
    // is assigned directly to the cht_obj object.
    cht_obj.get_data = function() {
        if (cht_obj.chart) {
            cht_obj.chart.showLoading("Loading Data");
        }
        // send data from all the select and input controls in the 'content' div
        // that have a name attribute.
        $.getJSON(cht_obj.data_url, $("#content select, #content input").serialize(), function(the_data) {
            cht_obj.server_data = the_data;
            cht_obj.redraw();
            cht_obj.chart.hideLoading();
        });
    };

    // Make the Refresh button a jQuery UI button and wire it to the get_data() funcation.
    // Have to remove any other handlers that were assigned to this button before 
    // (with the .off() method), since the button is part of the main page that is not 
    // replaced by AJAX queries.
    $("#refresh").button().off('click').click(cht_obj.get_data);

    return cht_obj;
}

// This creates a "chart" object for a text report.  The only method it needs to expose
// is the 'get_data' method; this method does not need to do anything, since the
// report is created from the HTML returned by the server in the 'AN.update_chart_html'
// method near the bottom of this file.
AN.chart_makers.base_report = function() {

    // Make the Refresh button a jQuery UI button and wire it 
    // to the method that gets the HTML.
    // Have to remove any other handlers that were assigned to this button before 
    // (with the .off() method), since the button is part of the main page that is not 
    // replaced by AJAX queries.
    $("#refresh").button().off('click').click(function(event) {
        AN.update_chart_html();
    });

    return {
        get_data: function() {}
    };

}

/********************************************************************
Specific Chart Making functions follow
*********************************************************************/

// Hourly Profile chart creator function
AN.chart_makers.HourlyProfile = function() {

    // Get the base chart and customize some options
    var cht = AN.chart_makers.base_chart();
    cht.chart_options.chart.type = "line";
    cht.chart_options.xAxis.title.text = "Hour of the Day";
    cht.chart_options.xAxis.categories = 
        ['12a', '1a', '2a', '3a', '4a', '5a', '6a', '7a', '8a', '9a', '10a', '11a', 
         '12p', '1p', '2p', '3p', '4p', '5p', '6p', '7p', '8p', '9p', '10p', '11p'];

    cht.redraw = function() { 
        // "this" won't refer to chart object if this function is
        // called through an event callback.

        // Set Y Axis title
        cht.chart.yAxis[0].setTitle( {text: cht.server_data.y_label}, false );

        // Set a Chart title indicating sensor, if there is a sensor selection involved
        if ($("#select_sensor").length) {
            var new_title = $("#select_sensor option:selected").text() + " Hourly Profile" + ": " + $("#select_bldg option:selected").text(); 
            cht.chart.setTitle( {text: new_title,
                                 style: {fontSize: '20px'}
                                });
        }

        // Remove all existing series and add new series
        AN.chart_makers.replace_series(cht.chart, cht.server_data.series, true);

        // if a normalized plot is occurring, set min and max of Y axis
        if ($("#normalize").is(':checked')) {
            cht.chart.yAxis[0].setExtremes(0, 100, false);
        } else {
            cht.chart.yAxis[0].setExtremes(null, null, false);
        }
        cht.chart.redraw();
    };

    $("#time_period").change(cht.get_data);
    $("#select_sensor").change(cht.get_data);
    $("#normalize").button();
    $("#normalize").change(cht.get_data);  // could be done locally, but easier at the server

    cht.chart = new Highcharts.Chart(cht.chart_options);

    return cht;
    
}

// Histogram chart object creator function
AN.chart_makers.Histogram = function() {

    // Get the base chart and customize some options
    var cht = AN.chart_makers.base_chart();
    cht.chart_options.yAxis.title.text = "% of Readings";
    cht.chart_options.yAxis.min = 0;
    cht.chart_options.chart.type = "line";

    cht.redraw = function() { 
        // "this" won't refer to chart object if this function is
        // called through an event callback.

        // Set Y Axis title
        cht.chart.xAxis[0].setTitle( {text: cht.server_data.x_label}, false );

        // Set a Chart title indicating sensor, if there is a sensor selection involved
        if ($("#select_sensor").length) {
            var new_title = $("#select_sensor option:selected").text() + " Histogram" + ": " + $("#select_bldg option:selected").text(); 
            cht.chart.setTitle( {text: new_title,
                                 style: {fontSize: '20px'}
                                });
        }

        // Remove all existing series and add new series
        AN.chart_makers.replace_series(cht.chart, cht.server_data.series, true);

        cht.chart.redraw();
    };

    $("#time_period").change(cht.get_data);
    $("#select_sensor").change(cht.get_data);

    cht.chart = new Highcharts.Chart(cht.chart_options);

    return cht;

}

// XY scatter plot chart object creator function
AN.chart_makers.XYplot = function() {

    // Get the base chart and customize some options
    var cht = AN.chart_makers.base_chart();
    cht.chart_options.chart.type = "scatter";
    cht.chart_options.plotOptions.series.marker.enabled = true;

    cht.redraw = function() { 
        // "this" won't refer to chart object if this function is
        // called through an event callback.

        // Set X and Y Axes titles
        cht.chart.xAxis[0].setTitle( {text: cht.server_data.x_label}, false );
        cht.chart.yAxis[0].setTitle( {text: cht.server_data.y_label}, false );

        // Set a Chart title 
        var new_title = $("#select_sensorY option:selected").text() + " vs. " + $("#select_sensorX option:selected").text(); 
        cht.chart.setTitle( {text: new_title,
                             style: {fontSize: '20px'}
                            });

        // Remove all existing series and add new series
        while (cht.chart.series.length) { cht.chart.series[0].remove() }
        $.each(cht.server_data.series, function(idx, a_series) {
            cht.chart.addSeries(a_series, false);
        });

        cht.chart.redraw();
    };

    $("#divide_date").datepicker({dateFormat: "mm/dd/yy"}).change(cht.get_data);

    $("#time_period").change(cht.get_data);
    $("#select_sensorX").change(cht.get_data);
    $("#select_sensorY").change(cht.get_data);
    $("#averaging_time").change(cht.get_data);

    cht.chart = new Highcharts.Chart(cht.chart_options);

    return cht;

}

// Time Series Chart object creator function
AN.chart_makers.TimeSeries = function() {

    // Get the base chart and customize some options
    var cht = AN.chart_makers.base_chart();

    cht.redraw = function() { 
        // "this" won't refer to chart object if this function is
        // called through an event callback.

        // Create array of Y axes
        var y_axes = [];
        $.each(cht.server_data.y_axes, function (idx, ax_id) {
            y_axes.push({
                id: ax_id,
                opposite: false,
                title: {
                    text: ax_id,
                    style: {fontSize: '16px'}
                }
            });
        });

        // Determine number of points to be plotted
        var pt_count = 0;
        $.each(cht.server_data.series, function(idx, ser) {
            pt_count += ser.data.length;
        });

        var opt;  // the chart options
        if (pt_count < 15000) {
            // Use the HighCharts chart
            opt = AN.chart_makers.cht_options();
            opt.title.text = "Time Series Plot: " + $("#select_bldg option:selected").text(); 
            opt.xAxis.title.text = "Date/Time (your computer's time zone)";
            opt.xAxis.type = "datetime";
            opt.chart.type = "line";
            opt.series = cht.server_data.series;
            opt.yAxis = y_axes;

            cht.chart = new Highcharts.Chart(opt);

        } else {
            // Large dataset, so use the HighStock chart
            opt = AN.chart_makers.cht_stock_options();
            opt.title.text = "Time Series Plot: " + $("#select_bldg option:selected").text(); 
            opt.series = cht.server_data.series;
            opt.yAxis = y_axes;
            cht.chart = new Highcharts.StockChart(opt);

        }

    };

    $("#time_period").change(cht.get_data);
    $("#select_sensor").bind('multiselectclose', cht.get_data);
    $("#averaging_time").change(cht.get_data);

    return cht;

}

// Dashboard report
AN.chart_makers.Dashboard= function() {

    var cht_obj = {
        get_data: function() {
            data_url = AN.make_chart_id_url() + "/data/";
            $.getJSON(data_url, function(dashConfig) {
                ANdash.createDashboard('dashboard', dashConfig);
            });
        }
    };

    $("#refresh").button().off('click').click(cht_obj.get_data);

    // have the get_data method called automatically every 10 minutes
    AN.refreshTimer = setInterval(cht_obj.get_data, 600000);

    return cht_obj

}


// Current Values report
AN.chart_makers.CurrentValues = function() {

    // have the chart refreshed automatically every 10 minutes
    AN.refreshTimer = setInterval(AN.update_chart_html, 600000);

    // Everything is done in the HTML returned by the server.  Nothing to do here.
    return AN.chart_makers.base_report();

}

// Export Data to Excel feature
AN.chart_makers.ExportData = function() {

    // base chart provides a lot of needed UI setup, so use it.
    var cht = AN.chart_makers.base_chart();

    // don't need the get_data routine so replace it with a do nothing function
    cht.get_data = function() {};

    $("#download_many").button().click( function() {
        window.location.href = AN.make_chart_id_url() + "/download_many/?" +
            $("#content select, #content input").serialize();
    });

    // Hide the refresh button
    $("#refresh").hide();

    return cht;
}

// base function for creating column charts that show a normalized value for a set of
// buildings.
AN.chart_makers.normalized_chart = function(norm_unit) {

    // Get the base chart and customize some options
    var cht = AN.chart_makers.base_chart();
    cht.chart_options.title.text = $("#select_chart option:selected").text();
    cht.chart_options.legend.enabled = false;
    cht.chart_options.yAxis.min = 0;
    cht.chart_options.chart.type = "column";
    cht.chart_options.xAxis.labels = {
                    rotation: -45,
                    align: 'right',
                    style: {fontSize: '13px'}
                    };

    cht.redraw = function() { 
        // "this" won't refer to chart object if this function is
        // called through an event callback.

        // set the building names to be the categories
        cht.chart.xAxis[0].setCategories(cht.server_data.bldgs);

        // set Y-axis title
        cht.chart.yAxis[0].setTitle({text: cht.server_data.value_units + norm_unit});

        // Remove all existing series and add new series
        AN.chart_makers.replace_series(cht.chart, cht.server_data.series);

        cht.chart.redraw();
    };

    $("#time_period").change(cht.get_data);

    cht.chart = new Highcharts.Chart(cht.chart_options);

    return cht;

}

// Normalized by Degree Day and Square foot chart object creator function
AN.chart_makers.NormalizedByDDbyFt2 = function() {
    return AN.chart_makers.normalized_chart('/ft2/degree-day');
}


// Normalized by Square foot chart object creator function
AN.chart_makers.NormalizedByFt2 = function() {
    return AN.chart_makers.normalized_chart('/ft2');
}


// ********************************* End of Chart Making Functions

// Causes a particular chart type and sensor to be selected.
AN.plot_sensor = function(chart_id, sensor_id) {

    // Select the chart and call the routine to load the HTML for this chart,
    // passing in the sensor id to be selected once the HTML is loaded.
    $("#select_chart").val(chart_id);
    AN.update_chart_html( null, {select_sensor: sensor_id} );
    
}

// initializes the chart, including assigning event handlers and acquiring 
// the chart data.
AN.init_chart = function() {

    // Extract the chart function name from the html and Make a chart object.
    var chart_func_name = $("#ChartFunc").text();
    AN.chart = AN.chart_makers[chart_func_name]();
    AN.chart.get_data();

}


// Updates the main content HTML based on the chart selected. 'params' is a
// Javascript object that can control aspects of the returned HTML, such as
// selecting a particular sensor in the sensor selection control.
AN.update_chart_html = function(event, params) {

    // Clear any refresh timer that may have been set
    if (typeof AN.refreshTimer != "undefined") clearInterval(AN.refreshTimer);

    // Default is for the Refresh button to Show
    $("#refresh").show();

    // Note: when params is not present in the argument list above, it is passed
    // as 'undefined' and causes no harm in the get() method (no query parameters
    // are created).
    $.get(AN.make_chart_id_url() + "/html/", params, function(chart_html) {

        $("#chart_content").html(chart_html);
        AN.init_chart();

    });

}

// Updates the list of charts appropriate for the building selected.
AN.update_chart_list = function() {

    // load the chart options from a AJAX query for the selected building
    $("#select_chart").load($("#BaseURL").text() + "chart_list/" +  $("#select_group").val() + 
        "/" +  $("#select_bldg").val() + "/", function () {

        // trigger the change event of the chart selector to get the 
        // selected option to process.
        $("#select_chart").trigger("change");

    });
    
}

// Updates the list of buildings associated with the Building Group selected.
AN.update_bldg_list = function() {
    
    // load the building choices from a AJAX query for the selected building group
    $("#select_bldg").load($("#BaseURL").text() + "bldg_list/" +  $("#select_group").val() + "/", function () {

        // trigger the change event of the building selector to get the 
        // selected option to process.
        $("#select_bldg").trigger("change");

    });
    
}

// function that runs when the document is ready.
$(function() {

    // Set up controls and functions to respond to events
    $("#select_group").change(AN.update_bldg_list);
    $("#select_bldg").change(AN.update_chart_list);
    $("#select_chart").change(AN.update_chart_html);

    // Prep the chart and get the chart data.
    AN.init_chart();

});
