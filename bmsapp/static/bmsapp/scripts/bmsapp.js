(function() {
  var REFRESH_MS, SENSOR_MULTI_CONFIG, _auto_recalc, _refresh_timer, inputs_changed, process_chart_change, set_visibility, update_bldg_list, update_chart_sensor_lists, update_results;

  window.AN = {};

  window.AN.plot_sensor = function(chart_id, sensor_id) {
    var sensor_ctrl;
    $("#select_chart").val(chart_id);
    if (sensor_id != null) {
      sensor_ctrl = $("#select_sensor");
      if ($("#select_sensor").attr("multiple") === "multiple") {
        sensor_ctrl.multiselect("destroy");
        sensor_ctrl.removeAttr("multiple");
        sensor_ctrl.val(sensor_id);
        sensor_ctrl.attr("multiple", "multiple");
        sensor_ctrl.multiselect(SENSOR_MULTI_CONFIG);
      } else {
        sensor_ctrl.val(sensor_id);
      }
    }
    return process_chart_change();
  };

  window.AN.plot_building_chart_sensor = function(bldg_id, chart_id, sensor_id) {
    $("#select_bldg").val(bldg_id);
    return update_chart_sensor_lists(null, chart_id, sensor_id);
  };

  _auto_recalc = true;

  inputs_changed = function() {
    if (_auto_recalc) {
      return update_results();
    }
  };

  update_results = function() {
    var url;
    $("body").css("cursor", "wait");
    url = ($("#BaseURL").text()) + "reports/results/";
    return $.getJSON(url, $("#content select, #content input").serialize()).done(function(results) {
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

  set_visibility = function(ctrl_list, show) {
    var ctrl, i, j, len, len1, results1, results2;
    if (show) {
      results1 = [];
      for (i = 0, len = ctrl_list.length; i < len; i++) {
        ctrl = ctrl_list[i];
        results1.push($("#" + ($.trim(ctrl))).show());
      }
      return results1;
    } else {
      results2 = [];
      for (j = 0, len1 = ctrl_list.length; j < len1; j++) {
        ctrl = ctrl_list[j];
        results2.push($("#" + ($.trim(ctrl))).hide());
      }
      return results2;
    }
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

  update_chart_sensor_lists = function(event, chart_id, sensor_id) {
    var url;
    url = ($("#BaseURL").text()) + "chart_sensor_list/" + ($("#select_group").val()) + "/" + ($("#select_bldg").val()) + "/";
    return $.getJSON(url, function(data) {
      $("#select_chart").html(data.charts);
      $("#select_sensor").html(data.sensors);
      $("#select_sensor_x").html(data.sensors);
      $("#select_sensor_y").html(data.sensors);
      if (chart_id != null) {
        return window.AN.plot_sensor(chart_id, sensor_id);
      } else {
        return process_chart_change();
      }
    });
  };

  update_bldg_list = function() {
    return $("#select_bldg").load(($("#BaseURL").text()) + "bldg_list/" + ($("#select_group").val()) + "/", function() {
      return $("#select_bldg").trigger("change");
    });
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
    $("#custom_dates").hide(0);
    $("#time_period").change(function() {
      if ($("input:radio[name=time_period]:checked").val() !== "custom") {
        return $("#custom_dates").hide();
      } else {
        return $("#custom_dates").show();
      }
    });
    $("#refresh").button().click(update_results);
    $("#normalize").button();
    $("#show_occupied").button();
    $("#divide_date").datepicker({
      dateFormat: "mm/dd/yy"
    });
    $("#download_many").button().click(function() {
      return window.location.href = (($("#BaseURL").text()) + "reports/results/?") + $("#content select, #content input").serialize();
    });
    $("#select_group").change(update_bldg_list);
    $("#select_bldg").change(update_chart_sensor_lists);
    $("#select_chart").change(process_chart_change);
    ctrls = ['averaging_time', 'averaging_time_export', 'normalize', 'show_occupied', 'select_sensor', 'select_sensor_x', 'select_sensor_y', 'averaging_time_xy', 'divide_date', 'time_period'];
    for (i = 0, len = ctrls.length; i < len; i++) {
      ctrl = ctrls[i];
      $("#" + ctrl).change(inputs_changed);
    }
    return process_chart_change();
  });

}).call(this);

//# sourceMappingURL=bmsapp.js.map
