(function() {
  var REFRESH_MS, SENSOR_MULTI_CONFIG, _auto_recalc, _loading_inputs, _refresh_timer, get_embed_link, handleUrlQuery, inputs_changed, process_chart_change, serializedInputs, set_visibility, update_bldg_list, update_chart_sensor_lists, update_results, urlQueryString,
    indexOf = [].indexOf || function(item) { for (var i = 0, l = this.length; i < l; i++) { if (i in this && this[i] === item) return i; } return -1; };

  _auto_recalc = true;

  _loading_inputs = false;

  inputs_changed = function() {
    if (_auto_recalc && !_loading_inputs) {
      if (urlQueryString() === '') {
        history.replaceState(null, null, "?".concat(serializedInputs()));
      } else if (serializedInputs() !== urlQueryString()) {
        history.pushState(null, null, "?".concat(serializedInputs()));
      }
      return update_results();
    }
  };

  serializedInputs = function() {
    return $("#content select, #content input").serialize();
  };

  update_results = function() {
    $("body").css("cursor", "wait");
    return $.getJSON(($("#BaseURL").text()) + "reports/results/", serializedInputs()).done(function(results) {
      $("body").css("cursor", "default");
      $("#results").empty();
      $("#results").html(results.html);
      return $.each(results.objects, function(ix, obj) {
        var obj_config, obj_type;
        obj_type = obj[0], obj_config = obj[1];
        switch (obj_type) {
          case 'plotly':
            return Plotly.plot(obj_config.renderTo, obj_config.data, obj_config.layout, obj_config.config);
          case 'dashboard':
            return ANdash.createDashboard(obj_config);
        }
      });
    }).fail(function(jqxhr, textStatus, error) {
      var err;
      $("body").css("cursor", "default");
      err = textStatus + ", " + error;
      return alert("Error Occurred: " + err);
    });
  };

  get_embed_link = function() {
    var link;
    link = '<script src="' + $("#BaseURL").text() + 'reports/embed/' + '?' + serializedInputs() + '" style="width: 930px" async></script>';
    return prompt("Here's the text to embed this report in another page:", link);
  };

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

  REFRESH_MS = 600000;

  _refresh_timer = setInterval(update_results, REFRESH_MS);

  SENSOR_MULTI_CONFIG = {
    minWidth: 300,
    selectedList: 3,
    close: inputs_changed
  };

  process_chart_change = function() {
    var selected_chart_option, sensor_ctrl, vis_ctrls;
    set_visibility(['refresh', 'ctrl_sensor', 'ctrl_avg', 'ctrl_avg_export', 'ctrl_normalize', 'ctrl_occupied', 'xy_controls', 'time_period', 'download_many'], false);
    selected_chart_option = $("#select_chart").find("option:selected");
    vis_ctrls = selected_chart_option.data("ctrls").split(",");
    set_visibility(vis_ctrls, true);
    clearInterval(_refresh_timer);
    if (selected_chart_option.data("timed_refresh") === 1) {
      _refresh_timer = setInterval(update_results, REFRESH_MS);
    }
    _auto_recalc = selected_chart_option.data("auto_recalc") === 1;
    sensor_ctrl = $("#select_sensor");
    if (selected_chart_option.data("multi_sensor") === 1) {
      if (sensor_ctrl.attr("multiple") !== "multiple") {
        sensor_ctrl.off();
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
      $("#results").empty();
    }
    return inputs_changed();
  };

  update_chart_sensor_lists = function(event) {
    var url;
    url = ($("#BaseURL").text()) + "chart-sensor-list/" + ($("#select_group").val()) + "/" + ($("#select_bldg").val()) + "/";
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

  update_bldg_list = function() {
    var url;
    url = ($("#BaseURL").text()) + "bldg-list/" + ($("#select_group").val()) + "/";
    return $.ajax({
      url: url,
      dataType: "html",
      async: !_loading_inputs,
      success: function(data) {
        $("#select_bldg").html(data);
        if (!_loading_inputs) {
          return $("#select_bldg").trigger("change");
        }
      }
    });
  };

  $(window).on("popstate", function(event) {
    handleUrlQuery();
    return update_results();
  });

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

  handleUrlQuery = function() {
    var element, i, len, name, params, sortedNames, value;
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
    _loading_inputs = true;
    for (i = 0, len = sortedNames.length; i < len; i++) {
      name = sortedNames[i];
      element = $('[name=\'' + name + '\']');
      if (params.hasOwnProperty(name)) {
        value = params[name];
        if (element.val() != value) {
          element.val(value);
          if (element.attr("multiple") === "multiple") {
            element.multiselect("refresh");
          }
        }
      }
      element.change();
    }
    _loading_inputs = false;
    return params;
  };

  $(function() {
    var ctrl, ctrls, d, i, len;
    $(document).tooltip();
    $("#time_period").buttonset();
    $("#start_date").datepicker({
      dateFormat: "mm/dd/yy"
    });
    d = new Date();
    $("#start_date").val((d.getMonth() + 1) + "/" + d.getDate() + "/" + d.getFullYear());
    $("#end_date").datepicker({
      dateFormat: "mm/dd/yy"
    });
    $("#time_period").change(function() {
      if ($("input:radio[name=time_period]:checked").val() !== "custom") {
        return $("#custom_dates").hide().find("select, input").prop("disabled", true);
      } else {
        return $("#custom_dates").show().find("select, input").prop("disabled", false);
      }
    });
    $("#time_period").change();
    $("#refresh").button().click(update_results);
    $("#get_embed_link").click(get_embed_link);
    $("#normalize").button();
    $("#show_occupied").button();
    $("#div_date").datepicker({
      dateFormat: "mm/dd/yy"
    });
    $("#download_many").button().click(function() {
      return window.location.href = (($("#BaseURL").text()) + "reports/results/?") + serializedInputs();
    });
    $("#select_group").change(update_bldg_list);
    $("#select_bldg").change(update_chart_sensor_lists);
    $("#select_chart").change(process_chart_change);
    ctrls = ['averaging_time', 'averaging_time_export', 'normalize', 'show_occupied', 'select_sensor', 'select_sensor_x', 'select_sensor_y', 'averaging_time_xy', 'div_date', 'time_period'];
    for (i = 0, len = ctrls.length; i < len; i++) {
      ctrl = ctrls[i];
      $("#" + ctrl).change(inputs_changed);
    }
    handleUrlQuery();
    history.replaceState(null, null, "?".concat(serializedInputs()));
    return inputs_changed();
  });

}).call(this);

//# sourceMappingURL=bmsapp.js.map
