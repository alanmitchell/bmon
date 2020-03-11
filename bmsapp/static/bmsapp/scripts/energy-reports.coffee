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

# Updates the list of buildings associated with the Organization selected.
update_bldg_list = ->
  org = $("#select_org").val()
  
  # Clear out Facility select box
  $("#select_bldg").empty()

  # Add buildings to the Select box
  add_bldg = (bldg) ->
    optn = new Option(bldg[0], bldg[1])
    $("#select_bldg").append(optn)
  # make sure this org is in the mapping, which was created the
  # night before.
  if _org_to_bldgs[org]?
    add_bldg bldg for bldg in _org_to_bldgs[org]
    # select the first building
    $("#select_bldg").val($("#select_bldg option:first").val())

# Updates the tabs that show the Report titles
update_report_list = ->
  # get selector values
  org = $("#select_org").val()
  bldg = $("#select_bldg").val()

  # Clear out all tabs
  $("#report-tab-list").empty()

  # Add reports to Tabs
  add_report = (rpt) ->
    html = """
    <li class="nav-item">
      <a class="nav-link" data-toggle="tab" href="##{ rpt.file_name }" role="tab">#{ rpt.title }</a>
    </li>
    """
    $("#report-tab-list").append html

  # Add building reports if this building is in the list
  if _bldg_reports[bldg]?
    add_report rpt for rpt in _bldg_reports[bldg]
  # Add Organization reports if this building is in the list
  if _org_reports[org]?
    add_report rpt for rpt in _org_reports[org]

  # Select the first tab
  $("#report-tab-list a:first").addClass("active")

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
      update_bldg_list()
      update_report_list()
    ).fail (jqxhr, textStatus, error) ->
      $("body").css "cursor", "default"   # remove hourglass cursor
      err = textStatus + ", " + error
      alert "Error Occurred: " + err

    $.getJSON(base_url + "building.json").done((results) ->
      _bldg_reports = results
      update_report_list()
    ).fail (jqxhr, textStatus, error) ->
      $("body").css "cursor", "default"   # remove hourglass cursor
      err = textStatus + ", " + error
      alert "Error Occurred: " + err

    $.getJSON(base_url + "organization.json").done((results) ->
      _org_reports = results
      update_report_list()
    ).fail (jqxhr, textStatus, error) ->
      $("body").css "cursor", "default"   # remove hourglass cursor
      err = textStatus + ", " + error
      alert "Error Occurred: " + err

    # Set up controls and functions to respond to events
    $("#select_org").change update_bldg_list
    $("#select_org").change update_report_list
    $("#select_bldg").change update_report_list

