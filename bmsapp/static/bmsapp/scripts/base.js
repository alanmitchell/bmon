(function() {
  // flag indicating whether this script should handle state
  // and location query parameter updating for the Organization
  // selector.
  var _handle_state, processOrgChange, setOrgFromQuery, updateLinks;

  _handle_state = true;

  // handle the history.popstate event
  $(window).on("popstate", function(event) {
    if (_handle_state) {
      return setOrgFromQuery();
    }
  });

  setOrgFromQuery = function() {
    var orgVal, params;
    params = new URLSearchParams(window.location.search);
    orgVal = params.get('select_org') || "0"; // default is 0, All Organizations
    $("#select_org").val(orgVal);
    return updateLinks(); // update menu links
  };

  processOrgChange = function() {
    var newLocation, newOrg, params;
    newOrg = $('#select_org').val();
    updateLinks(); // update menu bar links
    
    // update the query string in the address bar
    params = new URLSearchParams(window.location.search);
    if (params.has('select_org')) {
      params.set('select_org', newOrg);
    } else {
      params.append('select_org', newOrg);
    }
    newLocation = `${window.location.pathname}?${params}`;
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
