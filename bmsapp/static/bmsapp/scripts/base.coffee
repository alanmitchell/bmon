# flag indicating whether this script should handle state
# and location query parameter updating for the Organization
# selector.
_handle_state = true

# handle the history.popstate event
$(window).on "popstate", (event) ->
  if _handle_state
    setOrgFromQuery()

setOrgFromQuery = ->
  params = new URLSearchParams(window.location.search)
  orgVal = params.get('select_org') or "0"     # default is 0, All Organizations
  $("#select_org").val(orgVal)
  updateLinks()    # update menu links

processOrgChange = ->
  newOrg = $('#select_org').val()
  updateLinks()    # update menu bar links

  # update the query string in the address bar
  params = new URLSearchParams(window.location.search)
  if params.has('select_org')
    params.set('select_org', newOrg)
  else
    params.append('select_org', newOrg)
  newLocation = "#{window.location.pathname}?#{params}"
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

