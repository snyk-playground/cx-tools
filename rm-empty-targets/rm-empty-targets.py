#
# Example: Remove all empty targets in a Snyk group
#


import aiohttp
import asyncio
import logging
import os
import snyk
import sys
import traceback

# Keys for the config dict
key_is_configured = "is_configured"
key_config_status_msg = "config_status_msg"
key_is_dry_run = "is_dry_run"
key_snyktoken = "snyk_token"
key_snykgroup = "snyk_group"
key_snyk_rest_api = "snyk_rest_api"
key_concurrent_connection_limit = "concurrent_connection_limit"

##############################

# change this value to match the Snyk REST API version used:
key_api_version = "2024-01-23~beta"

##############################

async def main():
  session = None
  try:

    # Configuration
    config = get_config()
    if not config[key_is_configured]:
      log(config[key_config_status_msg])
      exit(1)

    if config[key_config_status_msg] != "":
      log(config[key_config_status_msg])

    snyktoken = config[key_snyktoken]
    snykgroup = config[key_snykgroup]

    # Client initialization
    # Use pysnyk clients for the v1 and rest APIs
    # this sets the session to include retries in case of api timeouts etc
    v1client = snyk.SnykClient(snyktoken, tries=3, delay=1, backoff=2)
    restclient = snyk.SnykClient(snyktoken, version=(key_api_version), url="https://api.snyk.io/rest", tries=3, delay=1,
                                 backoff=2)

    # Use aiohttp connection for new REST APIs not yet supported by pysnyk
    snyk_rest_api = config[key_snyk_rest_api]
    concurrent_connection_limit = config[key_concurrent_connection_limit]
    conn = aiohttp.TCPConnector(limit_per_host=concurrent_connection_limit)
    session_headers = {
      "Authorization": f"token {snyktoken}",
      "Content-Type": "application/json"
    }
    session = aiohttp.ClientSession(connector=conn, headers=session_headers)

    # Get orgs
    orgs = get_orgs(v1client, snykgroup)
    if orgs:
      groupname = orgs[0].group.name
    else:
      print(snykgroup + ": No orgs accessible in this group by your SNYK_TOKEN")
      print("")
      exit(1)

    # Delete targets for orgs #
    await delete_empty_targets_for_orgs(orgs, restclient, session, config)

  except Exception as e:
    traceback.print_exc()
  finally:
    try:
      if session is not None:
        await session.close()
    except:
      traceback.print_exc()

#######################################################################

def get_config():
  # return a dictionary of configuration settings
  config = {}
  config[key_is_configured] = False
  config[key_config_status_msg] = ""

  try:
    snyktoken = os.getenv('SNYK_TOKEN')
    config[key_snyktoken] = snyktoken
  except:
    config[key_config_status_msg] += "\nUnable to detect SNYK_TOKEN from environment. Exiting."
    return config

  snykgroup = ""
  try:
    snykgroup = sys.argv[1]
    config[key_snykgroup] = snykgroup
  except:
    if snykgroup == "":
        config[key_config_status_msg] += "\nNo SNYK_GROUP specified. Exiting."
        return config

  is_dry_run = True
  try: 
    unsafe_mode = sys.argv[2]
    if unsafe_mode == "--delete":
      is_dry_run = False
    elif unsafe_mode == "--dry-run":
      is_dry_run = True
    else:
      config[key_config_status_msg] += f"\nIgnoring invalid mode '{unsafe_mode}'"
      is_dry_run = True
  except:
    pass # default to 'dry-run' if mode not specified
  config[key_is_dry_run] = is_dry_run

  # logging
  #from http.client import HTTPConnection
  #HTTPConnection.debuglevel=1
  #logging.basicConfig()
  #logging.getLogger().setLevel(logging.DEBUG)
  #requests_log = logging.getLogger("requests.packages.urllib3")
  #requests_log.setLevel(logging.DEBUG)
  #requests_log.propagate = True

  # static config
  config[key_snyk_rest_api] = "https://api.snyk.io/rest"
  config[key_concurrent_connection_limit] = 10

  config[key_is_configured] = True
  return config

#######################################################################

def get_orgs(v1client, snykgroup):
  # return a list of the orgs in this Snyk group

  # get orgs and remove the phantom orgs that are really the groups
  orgs = v1client.organizations.all()
  orgs = [ y for y in orgs if hasattr(y.group,'id') ]
  # remove orgs that don't match the snykgroup
  orgs = [ y for y in orgs if y.group.id == snykgroup ]
  return orgs

#######################################################################

async def delete_empty_targets_for_orgs(orgs, restclient, session, config):
  # find and delete the empty targets in the specified orgs

  empty_targets = {}
  count_targets = 0
  for org in orgs:
    log(f"Checking {org.id} [ \"{org.name}\" | {org.slug} ]")
    empty_targets[org.id] = get_empty_targets(restclient, org.id)
    count_targets += len(empty_targets[org.id])

  if config[key_is_dry_run]:
      status_msg = f"[dry_run] {count_targets} target(s) to be deleted. Run with '--delete' to remove."
  else:
    log("")
    log(f"deleting {count_targets} target(s)...")
    log("")

    total_count_deleted = 0
    count_deleted = 0
    try:
      for target_org in empty_targets:
        count_deleted = await delete_empty_targets(session, config[key_snyk_rest_api], target_org, empty_targets[target_org])
        if count_deleted > 0:
          total_count_deleted += count_deleted
    finally:
      status_msg = f"{total_count_deleted} target(s) deleted."

  log("")
  log(status_msg)
  log("")

  for target_org in empty_targets:
    for target in empty_targets[target_org]:
      print(f"/orgs/{target_org}/targets/{target['id']}")

#######################################################################

def get_empty_targets(restclient, org_id):
  # return a list of empty targets for an org
  # 2022-03-10: There is not currently a filter to get just the empty
  #             targets, so we need to get both all of the targets and
  #             all non-empty targets, and then diff the lists to
  #             create the list of empty targets

  org_targets = f"orgs/{org_id}/targets"

  params = {"limit": 100, "excludeEmpty": False}
  all_targets = restclient.get_v3_pages(org_targets, params=params)

  params = {"limit": 100, "excludeEmpty": True}
  targets_with_projects = restclient.get_v3_pages(org_targets, params=params)

  empty_targets = []
  for target in all_targets:
    if target not in targets_with_projects:
      empty_targets.append(target)

  return empty_targets

#######################################################################

async def delete_empty_targets(session, snyk_api, org_id, targets):
  # delete the list of empty targets in the specified org

  # api_endpoint_version = "2024-01-23~beta"
  params = [('version', key_api_version)]
  count_deleted = 0

  for target in targets:
    target_url = f"{snyk_api}/orgs/{org_id}/targets/{target['id']}"
    log(f"...deleting target {target_url} ({target['attributes']['displayName']})")

    async with session.delete(target_url, params=params) as r:
      await r.text()
      count_deleted += 1

  return count_deleted
#######################################################################

def log(message):
  print("  " + message, file=sys.stderr)

#######################################################################

asyncio.run(main())
