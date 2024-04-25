#
# Example: Counts all of the targets in the specified SNYK_GROUP
#


import aiohttp
import asyncio
import click
import json
import logging
import os
import snyk
import sys
import traceback

# Keys for the config dict
key_is_configured = "is_configured"
key_config_status_msg = "config_status_msg"
key_snyktoken = "snyk_token"
key_snykgroup = "snyk_group"
key_snyk_rest_api = "snyk_rest_api"
key_concurrent_connection_limit = "concurrent_connection_limit"

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
    restclient = snyk.SnykClient(snyktoken, version="2024-04-22", url="https://api.snyk.io/rest", tries=3, delay=1,
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

    # Get unique targets for all orgs
    count_targets = await count_targets_for_orgs(orgs, restclient, session, config)

    print(f"Detected target counts for Snyk group {snykgroup} by origin:")
    for origin in count_targets:
      if count_targets[origin] > 0:
        print(f"{origin}: {count_targets[origin]}")

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

async def count_targets_for_orgs(orgs, restclient, session, config):

  count_targets = {}
  origins = [
    "cli",
    "acr",
    "artifactory-cr",
    "azure-repos",
    "bitbucket-cloud",
    "bitbucket-server",
    "digitalocean-cr",
    "docker-hub",
    "ecr",
    "gcr",
    "github",
    "github-cr",
    "github-enterprise",
    "gitlab",
    "gitlab-cr",
    "google-artifact-cr",
    "harbor-cr",
    "kubernetes",
    "nexus-cr",
    "quay-cr"
  ]

  for origin in origins:
      count_targets[origin] = 0

  fill_char = click.style('=')
  with click.progressbar(orgs,
                         length=len(orgs),
                         show_pos=True,
                         show_percent=True,
                         label='Analyzing orgs...',
                         fill_char=fill_char) as bar:
    for org in bar:
      #log(f"Checking {org.id} [ \"{org.name}\" | {org.slug} ]")
      targets = get_org_targets(restclient, org.id)
      for origin in origins:
          origin_targets = [ target for target in targets if target['relationships']['integration']['data']['attributes']['integration_type'] == origin ]
          count_targets[origin] += len(origin_targets)

  return count_targets


#######################################################################

def get_org_targets(restclient, org_id):

  org_targets = f"orgs/{org_id}/targets"

  params = {"limit": 100, "exclude_empty": False } # counts all targets, even if empty
  targets = restclient.get_rest_pages(org_targets, params=params)

  return targets

#######################################################################

def log(message):
  print("  " + message, file=sys.stderr)

#######################################################################

asyncio.run(main())
