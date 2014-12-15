# my object to contain all global variables and functions.  Minimizes
# global namespace pollution.
window.AN = {}

# Updates the list of charts appropriate for the building selected.
AN.update_chart_list = ->
  # load the chart options from a AJAX query for the selected building
  url = "#{$("#BaseURL").text()}chart_list/#{$("#select_group").val()}/#{$("#select_bldg").val()}/"
  $("#select_chart").load url, ->
    # trigger the change event of the chart selector to get the 
    # selected option to process.
    $("#select_chart").trigger "change"

# Updates the list of buildings associated with the Building Group selected.
AN.update_bldg_list = ->
  # load the building choices from a AJAX query for the selected building group
  $("#select_bldg").load "#{$("#BaseURL").text()}bldg_list/#{$("#select_group").val()}/", ->
    # trigger the change event of the building selector to get the 
    # selected option to process.
    $("#select_bldg").trigger "change"

# function that runs when the document is ready.
$ ->
  # Set up controls and functions to respond to events
  $("#select_group").change AN.update_bldg_list
  $("#select_bldg").change AN.update_chart_list
  # $("#select_chart").change AN.update_chart_html
