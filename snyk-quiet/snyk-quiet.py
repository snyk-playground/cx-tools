#
# Example: Turn off all notifications for the user that invokes the script
#
# WARNING:
#   This script will disable *all* Snyk notifications for the invoking user.
#   It will *not* ask for confirmation. Be sure this is what you want.
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
      orgs = v1client.organizations.all()

      await deactivate_user_notifications(session, orgs)

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

    # logging
    # from http.client import HTTPConnection
    # HTTPConnection.debuglevel=1
    # logging.basicConfig()
    # logging.getLogger().setLevel(logging.DEBUG)
    # requests_log = logging.getLogger("requests.packages.urllib3")
    # requests_log.setLevel(logging.DEBUG)
    # requests_log.propagate = True

    # static config
    config[key_snyk_rest_api] = "https://api.snyk.io/rest"
    config[key_concurrent_connection_limit] = 10

    config[key_is_configured] = True
    return config

#######################################################################

async def deactivate_user_notifications(session, orgs):

    mod_user_org_notification_settings_api = "https://snyk.io/api/v1/user/me/notification-settings/org"

    print(f"Deactivating your notifications for {len(orgs)} organizations...")

    fill_char = click.style('=')
    with click.progressbar(orgs,
            length=len(orgs),
            show_pos=True,
            show_percent=True,
            fill_char=fill_char) as bar:
        for org in bar:
            api_url = f"{mod_user_org_notification_settings_api}/{org.id}"
            settings_payload = {
                  "new-issues-remediations": {
                      "enabled": False,
                      "issueSeverity": "all",
                      "issueType": "all",
                      },
                  "project-imported": {
                      "enabled": False,
                      },
                  "test-limit": {
                      "enabled": False
                      },
                  "weekly-report": {
                      "enabled": False
                      }
                  }
            async with session.put(api_url, data=json.dumps(settings_payload)) as resp:
                if resp.status != 200:
                    print(f"{org.id}: Error {resp.status}")

#######################################################################

def log(message):
    print("  " + message, file=sys.stderr)

#######################################################################
asyncio.run(main())
