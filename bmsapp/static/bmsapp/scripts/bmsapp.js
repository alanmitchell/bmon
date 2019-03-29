(function() {
  // controls whether results are updated automatically or manually by
  // a direct call to 'update_results'
  var REFRESH_MS, SENSOR_MULTI_CONFIG, _auto_recalc, _loading_inputs, _refresh_timer, get_embed_link, handleUrlQuery, inputs_changed, process_chart_change, serializedInputs, set_visibility, update_bldg_list, update_chart_sensor_lists, update_results, urlQueryString,
    indexOf = [].indexOf;

  _auto_recalc = true;

  // flags whether inputs are in the process of being loaded
  _loading_inputs = false;

  // Called when inputs that affect the results have changed
  inputs_changed = function() {
    if (_auto_recalc && !_loading_inputs) {
      // update the window location url if needed
      if (urlQueryString() === '') {
        history.replaceState(null, null, "?".concat(serializedInputs()));
      } else if (serializedInputs() !== urlQueryString()) {
        history.pushState(null, null, "?".concat(serializedInputs()));
      }
      // update the results display
      return update_results();
    }
  };

  serializedInputs = function() {
    return $("#content select, #content input").serialize();
  };

  
  // Updates the results portion of the page
  update_results = function() {
    $("body").css("cursor", "wait"); // show hourglass
    return $.getJSON(`${$("#BaseURL").text()}reports/results/`, serializedInputs()).done(function(results) {
      
      // load the returned HTML into the results div, but empty first to ensure
      // event handlers, etc. are removed
      $("body").css("cursor", "default"); // remove hourglass cursor
      $("#results").empty();
      $("#results").html(results.html);
      
      // Loop through the returned JavaScript objects to create and make them
      return $.each(results.objects, function(ix, obj) {
        var obj_config, obj_type;
        [obj_type, obj_config] = obj;
        switch (obj_type) {
          case 'plotly':
            return Plotly.plot(obj_config.renderTo, obj_config.data, obj_config.layout, obj_config.config);
          case 'dashboard':
            return ANdash.createDashboard(obj_config);
        }
      });
    }).fail(function(jqxhr, textStatus, error) {
      var err;
      $("body").css("cursor", "default"); // remove hourglass cursor
      err = textStatus + ", " + error;
      return alert("Error Occurred: " + err);
    });
  };

  // copies a link to embed the current report into another page
  get_embed_link = function() {
    var link_comment, link_dialog, link_text, title;
    title = document.getElementById("report_title");
    if (title !== null) {
      link_comment = `<!--- Embedded BMON Chart: ${title.innerText} --->`;
    } else {
      link_comment = "<!--- Embedded BMON Chart --->";
    }
    link_text = '<script src="' + $("#BaseURL").text() + 'reports/embed/' + '?' + serializedInputs() + '" style="width: 930px" async></script>';
    link_dialog = $(`<div class='popup' title='Copy and paste this text to embed this view in a Custom Report:'><textarea id='embed_link' rows=5 style='width: 99%;font-size: 85%;resize: vertical'>${link_comment}&#010;${link_text}&#010;</textarea></div>`);
    //link_dialog.text("#{link_comment}#{link_text}")
    return link_dialog.dialog({
      modal: true,
      width: 750,
      buttons: {
        "Copy to Clipboard": function() {
          var success;
          $("#embed_link").select();
          return success = document.execCommand("copy");
        }
      },
      close: function() {
        return $(this).dialog('destroy').remove();
      }
    });
  };

  
  // Sets the visibility of elements in the list of ids 'ctrl_list'.
  // If 'show' is true then the element is shown, hidden otherwise.
  set_visibility = function(ctrl_list, show) {
    var ctrl, element, i, len;
    for (i = 0, len = ctrl_list.length; i < len; i++) {
      ctrl = ctrl_list[i];
      element = document.getElementById($.trim(ctrl));
      if (show) {
        $(element).show().find("select, input:visible").prop("disabled", false);
      } else {
        $(element).hide().find("select, input").prop("disabled", true);
      }
    }
    return show;
  };

  // A timer used by some charts to do a timed refresh of the results.
  REFRESH_MS = 600000; // milliseconds between timed refreshes

  _refresh_timer = setInterval(update_results, REFRESH_MS);

  // The configuration options for a the multiselect sensor input
  SENSOR_MULTI_CONFIG = {
    minWidth: 300,
    selectedList: 3,
    close: inputs_changed
  };

  // Handles actions required when the chart type changes.  Mostly sets
  // the visibility of controls.
  process_chart_change = function() {
    var selected_chart_option, sensor_ctrl, vis_ctrls;
    // start by hiding all input controls
    set_visibility(['refresh', 'ctrl_sensor', 'ctrl_avg', 'ctrl_avg_export', 'ctrl_normalize', 'ctrl_occupied', 'xy_controls', 'time_period', 'download_many'], false);
    // get the chart option control that is selected.  Then use the data
    // attributes of that option element to configure the user interface.
    selected_chart_option = $("#select_chart").find("option:selected");
    // list of controls that should be visible
    vis_ctrls = selected_chart_option.data("ctrls").split(",");
    set_visibility(vis_ctrls, true);
    // Should timed refresh be set?
    clearInterval(_refresh_timer); // clear any old timer
    if (selected_chart_option.data("timed_refresh") === 1) {
      _refresh_timer = setInterval(update_results, REFRESH_MS);
    }
    
    // set auto recalculation
    _auto_recalc = selected_chart_option.data("auto_recalc") === 1;
    // Set sensor selector to multiple if needed
    sensor_ctrl = $("#select_sensor");
    if (selected_chart_option.data("multi_sensor") === 1) {
      if (sensor_ctrl.attr("multiple") !== "multiple") {
        sensor_ctrl.off(); // remove any existing handlers
        sensor_ctrl.attr("multiple", "multiple");
        sensor_ctrl.multiselect(SENSOR_MULTI_CONFIG);
      }
    } else {
      if (sensor_ctrl.attr("multiple") === "multiple") {
        sensor_ctrl.multiselect("destroy");
        sensor_ctrl.removeAttr("multiple");
        sensor_ctrl.off().change(inputs_changed);
      }
    }
    if (_auto_recalc === false) {
      // if manual recalc, then blank out the results area to clear our remnants
      // from last chart
      $("#results").empty();
    }
    // the chart type changed so indicated that inputs have changed
    return inputs_changed();
  };

  // Updates the list of charts and sensors appropriate for the building selected.
  // If chart_id and sensor_id are passed, selects that chart and sensor after
  // updating the list of apprpriate charts and sensors.
  update_chart_sensor_lists = function(event) {
    var url;
    // load the options from a AJAX query for the selected building
    url = `${$("#BaseURL").text()}chart-sensor-list/${$("#select_group").val()}/${$("#select_bldg").val()}/`;
    return $.ajax({
      url: url,
      dataType: "json",
      async: !_loading_inputs,
      success: function(data) {
        $("#select_chart").html(data.charts);
        $("#select_sensor").html(data.sensors);
        $("#select_sensor_x").html(data.sensors);
        $("#select_sensor_y").html(data.sensors);
        return process_chart_change();
      }
    });
  };

  // Updates the list of buildings associated with the Building Group selected.
  update_bldg_list = function() {
    var url;
    // load the building choices from a AJAX query for the selected building group
    url = `${$("#BaseURL").text()}bldg-list/${$("#select_org").val()}/${$("#select_group").val()}/`;
    return $.ajax({
      url: url,
      dataType: "html",
      async: !_loading_inputs,
      success: function(data) {
        $("#select_bldg").html(data);
        if (!_loading_inputs) {
          // trigger the change event of the building selector to get the 
          // selected option to process.
          return $("#select_bldg").trigger("change");
        }
      }
    });
  };

  // handle the history.popstate event
  $(window).on("popstate", function(event) {
    handleUrlQuery();
    return update_results();
  });

  // extract the query string portion of the current window's url
  urlQueryString = function() {
    var queryStart, url;
    url = window.location.href;
    queryStart = url.indexOf('?') + 1;
    if (queryStart > 0) {
      return url.substr(queryStart);
    } else {
      return '';
    }
  };

  // parse and handle the url query string
  handleUrlQuery = function() {
    var element, i, len, name, new_value, old_value, params, sortedNames;
    params = {};
    $.each(urlQueryString().replace(/\+/g, '%20').split('&'), function() {
      var name, name_value, value;
      name_value = this.split('=');
      name = decodeURIComponent(name_value[0]);
      value = name_value.length > 1 ? decodeURIComponent(name_value[1]) : null;
      if (!(name in params)) {
        params[name] = [];
      }
      params[name].push(value);
    });
    
    // sort the params so their events fire properly
    sortedNames = (function() {
      var name, names;
      names = ['select_group', 'select_bldg', 'select_chart'];
      for (name in params) {
        if (indexOf.call(names, name) < 0) {
          names.push(name);
        }
      }
      return names;
    })();
    
    // update control values
    _loading_inputs = true;
    for (i = 0, len = sortedNames.length; i < len; i++) {
      name = sortedNames[i];
      element = $('[name=\'' + name + '\']');
      if (params.hasOwnProperty(name)) {
        new_value = params[name];
        if (element.parent().attr("class") === "ui-buttonset") {
          old_value = element.filter(":radio:checked").val();
        } else {
          old_value = element.val();
        }
        if (old_value != new_value) {
          element.val(new_value);
          if (element.attr("multiple") === "multiple") {
            element.multiselect("refresh");
          }
        }
      }
      element.change(); // trigger the change event
    }
    _loading_inputs = false;
    return params;
  };

  
  // ---------------------------------------------------------------
  // function that runs when the document is ready.
  $(function() {
    var ctrl, ctrls, d, i, len;
    // enable jQuery UI tooltips
    $(document).tooltip();
    // Configure many of the elements that commonly appear in chart configuration
    // form.
    $("#time_period").buttonset();
    // Related to selecting the range of dates to chart
    $("#start_date").datepicker({
      dateFormat: "mm/dd/yy"
    });
    d = new Date(); // current date to use for a default for Start Date
    $("#start_date").val((d.getMonth() + 1) + "/" + d.getDate() + "/" + d.getFullYear());
    $("#end_date").datepicker({
      dateFormat: "mm/dd/yy"
    });
    
    // Show and Hide custom date range selector
    $("#time_period").change(function() {
      if ($("input:radio[name=time_period]:checked").val() !== "custom") {
        return $("#custom_dates").hide().find("select, input").prop("disabled", true);
      } else {
        return $("#custom_dates").show().find("select, input").prop("disabled", false);
      }
    });
    $("#time_period").change();
    
    // make refresh button a jQuery button & call update when clicked
    $("#refresh").button().click(update_results);
    $("#get_embed_link").click(get_embed_link);
    $("#normalize").button(); // checkbox to create normalized (0-100%) hourly profile
    $("#show_occupied").button(); // checkbox to create normalized (0-100%) hourly profile
    $("#div_date").datepicker({
      dateFormat: "mm/dd/yy" // for xy plot
    });
    
    // special handling of the Excel Export button because the content for this report
    // is not displayed in a normal results div.
    $("#download_many").button().click(function() {
      return window.location.href = `${$("#BaseURL").text()}reports/results/?` + serializedInputs();
    });
    $("#select_org").change(update_bldg_list);
    $("#select_group").change(update_bldg_list);
    $("#select_bldg").change(update_chart_sensor_lists);
    $("#select_chart").change(process_chart_change);
    // Set up change handlers for inputs.
    ctrls = ['averaging_time', 'averaging_time_export', 'normalize', 'show_occupied', 'select_sensor', 'select_sensor_x', 'select_sensor_y', 'averaging_time_xy', 'div_date', 'time_period'];
    for (i = 0, len = ctrls.length; i < len; i++) {
      ctrl = ctrls[i];
      $(`#${ctrl}`).change(inputs_changed);
    }
    // Handle any query parameters on the url
    handleUrlQuery();
    
    // Update the window's url to reflect the current inputs state
    history.replaceState(null, null, "?".concat(serializedInputs()));
    
    // Update the display based on the inputs
    return inputs_changed();
  });

}).call(this);
