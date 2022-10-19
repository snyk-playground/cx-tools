#
# Example: export a list of all users and service accounts in the specified group to CSV
#          (uses https://snyk.docs.apiary.io/#reference/groups/list-members-in-a-group/list-all-members-in-a-group)
#
# Usage: python userlist.py [Snyk group ID]
#
# Requires the following environment variables to be set:
#   SNYK_GROUP - Group ID for the Snyk Group user list. If specified on the command line, will override this value
#   SNYK_TOKEN - API token with admin access to the SNYK_GROUP
#
#


import aiohttp
import asyncio
from io import StringIO
import os
import pandas as pd
import sys
import traceback


# Keys for the config dict
key_is_configured = "is_configured"
key_config_status_msg = "config_status_msg"
key_snyktoken = "snyk_token"
key_snykgroup = "snyk_group"
key_snyk_api = "snyk_api"
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

      snykgroup = config[key_snykgroup]
      
      # Client initialization
      concurrent_connection_limit = config[key_concurrent_connection_limit]
      conn = aiohttp.TCPConnector(limit_per_host=concurrent_connection_limit)
      snyktoken = config[key_snyktoken]
      session_headers = {
              "Authorization": f"token {snyktoken}",
              "Content-Type": "application/json"
              }
      session = aiohttp.ClientSession(connector=conn, headers=session_headers)

      users = await get_group_users(session, config)
      userlist_df = get_userlist_dataframe(snykgroup, users)
      userlist_df.to_csv(sys.stdout,index=False)
    
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

    try:
        try:
            snykgroup = sys.argv[1]
        except:
            snykgroup = os.getenv('SNYK_GROUP')
    except:
        config[key_config_status_msg] += "\nNo SNYK_GROUP specified. Exiting."
        return config

    if snykgroup != "":
        config[key_snykgroup] = snykgroup
    else:
        config[key_config_status_msg] += "\nNo SNYK_GROUP specified. Exiting."
        return config

    # static config
    config[key_snyk_api] = "https://api.snyk.io/api/v1"
    config[key_concurrent_connection_limit] = 10

    config[key_is_configured] = True
    return config

#######################################################################

async def get_group_users(session,config):

    snyk_api = config[key_snyk_api]
    snykgroup= config[key_snykgroup]
    api_url = f"{snyk_api}/group/{snykgroup}/members"
    async with session.get(api_url) as resp:
        if resp.status != 200:
            print(f"{snykgroup}: Error {resp.status}")
            exit(1)
        users = await resp.json()

    # Service accounts don't have an email address, so add an indicator to the output
    for user in users:
        if user['email'] is None:
            email = "<service account>"
        else:
            email = user['email']

        user['email'] = email

    return users

#######################################################################

def get_userlist_dataframe(snykgroup, users):
    userlist = ["group_id,user_email,user_name,user_id\n"]
    for user in users:
        userlist.append(f"{snykgroup},{user['email']},{user['username']},{user['id']}\n")
        buffer = ''.join(userlist)
    df = pd.read_csv(StringIO(buffer),header=0,sep=",")
    df.sort_values(by=['user_email'], inplace=True)
    return df      
#######################################################################

def log(message):
    print("  " + message, file=sys.stderr)

#######################################################################
asyncio.run(main())
