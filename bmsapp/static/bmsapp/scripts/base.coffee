# flag indicating whether this script should handle state
# and location query parameter updating for the Organization
# selector.
_handle_state = true

# handle the history.popstate event
$(window).on "popstate", (event) ->
  if _handle_state
    setOrgFromQuery()
    location.reload()

# Returns an object containing the query parameters from 'url_str'.
# The keys of the object are the names of the query parameters.
# The value of each element in the object is an array, as one parameter
# can have multiple values.
# We are avoiding the use of more modern Javascript functions such as URLSearchParms
# in order to maintain compatibility with Internet Explorer.
queryParams = (url_str) ->
  queryStart = url_str.indexOf('?') + 1
  if queryStart > 0
    q = url_str.substr(queryStart)
  else
    q = ''
  q_parts = q.replace(/\+/g, '%20').split('&')
  params = {}
  pushParam = (p) ->
    name_value = p.split("=")
    name = decodeURIComponent(name_value[0])
    value = if name_value.length > 1 then decodeURIComponent(name_value[1]) else null
    if !(name of params)
      params[name] = []
    params[name].push value
  pushParam p for p in q_parts
  params

setOrgFromQuery = ->
  params = queryParams(window.location.href)
  if ('select_org' of params)
    orgVal = params['select_org'][0]
  else
    orgVal = "0"   # default, all organizations
  $("#select_org").val(orgVal)
  updateLinks()    # update menu links

processOrgChange = ->
  newOrg = $('#select_org').val()
  updateLinks()    # update menu bar links

  # Update the window location URL
  ser_inputs = $("#wrap select, #wrap input").serialize()
  newLocation = window.location.pathname + "?" + ser_inputs
  window.history.pushState({}, '', newLocation)

updateLinks = ->
  # Update the menu links to include a "select_org" query string with this value
  link_elems = (elem for elem in $('#nav_links a') when elem.getAttribute('href')?)
  orgVal = $('#select_org').val()
  for elem in link_elems
    base_link = elem.getAttribute('href').split('/')[1]
    elem.setAttribute("href", "/#{base_link}/?select_org=#{orgVal}")

$ ->
  # If this is the report page, don't handle the state and location
  # bar, as the script in the report page does that already
  if (window.location.pathname.indexOf "/reports/") >= 0
    _handle_state = false

  # Handle any query parameters on the url
  if _handle_state
    setOrgFromQuery()

  # Set up change handler for Organization select
  if _handle_state
    $("#select_org").change processOrgChange
  else
    $("#select_org").change updateLinks

