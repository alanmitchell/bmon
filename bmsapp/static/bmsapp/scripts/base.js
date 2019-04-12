(function() {
  // flag indicating whether this script should handle state
  // and location query parameter updating for the Organization
  // selector.
  var _handle_state, processOrgChange, queryParams, setOrgFromQuery, updateLinks;

  _handle_state = true;

  // handle the history.popstate event
  $(window).on("popstate", function(event) {
    if (_handle_state) {
      setOrgFromQuery();
      return location.reload();
    }
  });

  // Returns an object containing the query parameters from 'url_str'.
  // The keys of the object are the names of the query parameters.
  // The value of each element in the object is an array, as one parameter
  // can have multiple values.
  // We are avoiding the use of more modern Javascript functions such as URLSearchParms
  // in order to maintain compatibility with Internet Explorer.
  queryParams = function(url_str) {
    var i, len, p, params, pushParam, q, q_parts, queryStart;
    queryStart = url_str.indexOf('?') + 1;
    if (queryStart > 0) {
      q = url_str.substr(queryStart);
    } else {
      q = '';
    }
    q_parts = q.replace(/\+/g, '%20').split('&');
    params = {};
    pushParam = function(p) {
      var name, name_value, value;
      name_value = p.split("=");
      name = decodeURIComponent(name_value[0]);
      value = name_value.length > 1 ? decodeURIComponent(name_value[1]) : null;
      if (!(name in params)) {
        params[name] = [];
      }
      return params[name].push(value);
    };
    for (i = 0, len = q_parts.length; i < len; i++) {
      p = q_parts[i];
      pushParam(p);
    }
    return params;
  };

  setOrgFromQuery = function() {
    var orgVal, params;
    params = queryParams(window.location.href);
    if ('select_org' in params) {
      orgVal = params['select_org'][0];
    } else {
      orgVal = "0"; // default, all organizations
    }
    $("#select_org").val(orgVal);
    return updateLinks(); // update menu links
  };

  processOrgChange = function() {
    var newLocation, newOrg, ser_inputs;
    newOrg = $('#select_org').val();
    updateLinks(); // update menu bar links
    
    // Update the window location URL
    ser_inputs = $("#wrap select, #wrap input").serialize();
    newLocation = `${window.location.pathname}?${ser_inputs}`;
    return window.history.pushState({}, '', newLocation);
  };

  updateLinks = function() {
    var base_link, elem, i, len, link_elems, orgVal, results;
    // Update the menu links to include a "select_org" query string with this value
    link_elems = (function() {
      var i, len, ref, results;
      ref = $('#nav_links a');
      results = [];
      for (i = 0, len = ref.length; i < len; i++) {
        elem = ref[i];
        if (elem.getAttribute('href') != null) {
          results.push(elem);
        }
      }
      return results;
    })();
    orgVal = $('#select_org').val();
    results = [];
    for (i = 0, len = link_elems.length; i < len; i++) {
      elem = link_elems[i];
      base_link = elem.getAttribute('href').split('/')[1];
      results.push(elem.setAttribute("href", `/${base_link}/?select_org=${orgVal}`));
    }
    return results;
  };

  $(function() {
    // If this is the report page, don't handle the state and location
    // bar, as the script in the report page does that already
    if ((window.location.pathname.indexOf("/reports/")) >= 0) {
      _handle_state = false;
    }
    // Handle any query parameters on the url
    if (_handle_state) {
      setOrgFromQuery();
    }
    // Set up change handler for Organization select
    if (_handle_state) {
      return $("#select_org").change(processOrgChange);
    } else {
      return $("#select_org").change(updateLinks);
    }
  });

}).call(this);
