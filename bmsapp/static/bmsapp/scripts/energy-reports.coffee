# Coffee Script file that provides the functionality for the Energy Reports
# page.  The Javascript version of this is included in the 'energy-reports.html'
# template.

# Variables needed for identifying availabe reports

# The base URL where building/organization mapping info is available and
# reports are available
_base_url = ""

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
    update_report_list()

# Updates the tabs that show the Report titles
update_report_list = ->
  # get selector values
  org = $("#select_org").val()
  bldg = $("#select_bldg").val()

  # Clear out all tabs
  $("#report-tab-list").empty()

  # Add reports to Tabs
  add_report = (rpt, rpt_type) ->
    html = """
    <li class="nav-item">
      <a class="nav-link" data-toggle="tab" href="##{ rpt_type }-#{ rpt.file_name }" role="tab">#{ rpt.title }</a>
    </li>
    """
    $("#report-tab-list").append html

  # Add building reports if this building is in the list
  # Track # of reports.
  rpt_count = 0
  if _bldg_reports[bldg]?
    add_report(rpt, "B") for rpt in _bldg_reports[bldg]
    rpt_count += 1
  
  # Add Organization reports if this building is in the list
  if _org_reports[org]?
    add_report(rpt, "O") for rpt in _org_reports[org]
    rpt_count += 1

  if rpt_count > 0
    $("#report-tabs").show()
    $("#iframe-related").show()

    # add a handler for the click event on all of the a links associated
    # with the tabs.
    $("#report-tab-list a").click load_report

    # Select the first tab
    $("#report-tab-list a:first").addClass("active").click()

  else
    # No reports, so hide tabs and iFrame
    $("#report-tabs").hide()
    $("#iframe-related").hide()

load_report = ->
  # href attribute contains info about where the report is located
  report_info = $(this).attr("href").substring(1)
  report_file_name = report_info.substring(2)
  if report_info.substring(0, 1) == "B"
    report_url = "#{ _base_url }building/#{ $("#select_bldg").val() }/#{ report_file_name }"
  else
    report_url = "#{ _base_url }organization/#{ $("#select_org").val() }/#{ report_file_name }"

  $("#report-content").attr("src", report_url)
  $("#print-link").attr("href", report_url)     # update link to printable version of report

# ---------------------------------------------------------------
# function that runs when the document is ready.
$ ->

  # Get the data files from the Report server, first getting the base URL from
  # the hidden span element on this page.
  _base_url = $("#energy-reports-url").text()
  # only acquire data if there is a Base URL.
  if _base_url.length > 0

    $.getJSON(_base_url + "org_to_bldgs.json").done((results) ->
      _org_to_bldgs = results
      update_bldg_list()
      update_report_list()
    ).fail (jqxhr, textStatus, error) ->
      $("body").css "cursor", "default"   # remove hourglass cursor
      err = textStatus + ", " + error
      alert "Error Occurred: " + err

    $.getJSON(_base_url + "building.json").done((results) ->
      _bldg_reports = results
      update_report_list()
    ).fail (jqxhr, textStatus, error) ->
      $("body").css "cursor", "default"   # remove hourglass cursor
      err = textStatus + ", " + error
      alert "Error Occurred: " + err

    $.getJSON(_base_url + "organization.json").done((results) ->
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

  else
    $("#bldg-selection").hide()
    $("#report-tabs").hide()
    $("#iframe-related").hide()
        