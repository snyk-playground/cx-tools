#
# Example: emit a list of projects who have not tested after a specified date
#
# Usage: python snyk-not-tested-since.py <group id> <date>
#
# where <group id> is the Snyk group you want to check (your API key must be a group admin)
# and <date> is the date you want to compare your project lastTestedDate against (YYYY-MM-DD)
#

import aiohttp
import asyncio
import datetime
from dateutil import parser
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
key_targetdate = "target_date"
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
    restclient = snyk.SnykClient(snyktoken, version="experimental", url="https://api.snyk.io/rest", tries=3, delay=1,
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

    print(f"The following projects have not tested since {config[key_targetdate]} or earlier:")
    await check_orgs(orgs, restclient, session, config)

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

  targetdate = ""
  try:
    targetdate = sys.argv[2]
    config[key_targetdate] = targetdate
  except:
    if targetdate == "":
        config[key_config_status_msg] += "\nUnrecognized target date format. Use YYYY-MM-DD."
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


async def check_orgs(orgs, restclient, session, config):

    check_date = parser.isoparse(config[key_targetdate])
    base_url = "https://snyk.io"
    for org in orgs:
        org_base_url = f"{base_url}/org/{org.slug}"
        for project in org.projects.all():
            project_url = f"{org_base_url}/project/{project.id}"
            last_tested_date = parser.isoparse(project.lastTestedDate)
            if last_tested_date.date() <= check_date.date():
                project_details = f"{project_url}: last tested {project.lastTestedDate}"
                project_status = " "
                if (not project.isMonitored):
                    project_status += "[inactive] "
                if (project.readOnly):
                    project_status += "[read only] "
                print(project_details + str.strip(project_status))


#######################################################################

def log(message):
  print("   " + message, file=sys.stderr)

#######################################################################

asyncio.run(main())
