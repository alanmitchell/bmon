# Coffee Script file that provides the functionality for the Energy Reports
# page.  The Javascript version of this is included in the 'energy-reports.html'
# template.

# Variables needed for identifying availabe reports

# An object mapping organization ID to a list of buildings associated with
# that organization.
_org_to_bldgs = {}

# An object mapping building ID to a list of building reports
_bldg_reports = {}

# An object mapping organization ID to a list of organization reports
_org_reports = {}

# ---------------------------------------------------------------
# function that runs when the document is ready.
$ ->

  # Get the data files from the Report server, first getting the base URL from
  # the hidden span element on this page.
  base_url = $("#energy-reports-url").text()
  # only acquire data if there is a Base URL.
  if base_url.length > 0

    $.getJSON(base_url + "org_to_bldgs.json").done((results) ->
      _org_to_bldgs = results
    ).fail (jqxhr, textStatus, error) ->
      $("body").css "cursor", "default"   # remove hourglass cursor
      err = textStatus + ", " + error
      alert "Error Occurred: " + err

    $.getJSON(base_url + "building.json").done((results) ->
      _bldg_reports = results
    ).fail (jqxhr, textStatus, error) ->
      $("body").css "cursor", "default"   # remove hourglass cursor
      err = textStatus + ", " + error
      alert "Error Occurred: " + err

    $.getJSON(base_url + "organization.json").done((results) ->
      _org_reports = results
      $("#debug-out").text JSON.stringify(_org_reports)
    ).fail (jqxhr, textStatus, error) ->
      $("body").css "cursor", "default"   # remove hourglass cursor
      err = textStatus + ", " + error
      alert "Error Occurred: " + err

