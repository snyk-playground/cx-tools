import json
import os
import requests

SNYK_V1_API_BASE_URL="https://api.snyk.io/v1"

def build_headers():
    headers = {
        'Content-Type': 'application/json; charset=utf-8',
        'Authorization': 'token {0}'.format(os.getenv('SNYK_TOKEN'))
    }
    return headers


def org_integrations(org_id):
    response = None
    url = f'{SNYK_V1_API_BASE_URL}/org/{org_id}/integrations'
    response = requests.request("GET", url, headers=build_headers())
    if response.status_code != 200:
        print(response.text)
    return response


def get_org_integration_settings(org_id, integration_id):
    response = None
    url = f'{SNYK_V1_API_BASE_URL}/org/{org_id}/integrations/{integration_id}/settings'
    response = requests.request("GET", url, headers=build_headers())
    if response.status_code != 200:
        print(response.text)
    return response


# Update the config settings for a specified org and integration id
def update_org_integration_settings(org_id, integration_id, values):
    response = None
    url = f'{SNYK_V1_API_BASE_URL}/org/{org_id}/integrations/{integration_id}/settings'
    response = requests.put(url, headers=build_headers(), json=values)
    if response.status_code != 200:
        print(response.text)
    return response


def org_members(org_id):
    response = None
    try:
        url = f'{SNYK_V1_API_BASE_URL}/org/{org_id}/members?includeGroupAdmins=true'
        return requests.request("GET", url, headers=build_headers())
    except Exception:
        print(json.dumps(response, indent=4))


# Create the target organisation into which the pipeline jobs will commit scan results, thus yielding targets and
# projects
def create_organization(args, group):
    url = f'{SNYK_V1_API_BASE_URL}/org'
    if args["template_org_id"] is None:
        payload = {
            'name': '{0}'.format(args["org_name"]),
            'groupId': '{0}'.format(group["id"])
        }
    else:
        payload = {
            'name': '{0}'.format(args["org_name"]),
            'groupId': '{0}'.format(group["id"]),
            'sourceOrgId': '{0}'.format(args["template_org_id"])
        }
    return requests.post(url, headers=build_headers(), json=payload)


# Find the id for the named group role that will apply to the service account created within the org
def get_group_role_id(args, group_id, role_name):
    url = f'{SNYK_V1_API_BASE_URL}/group/{group_id}/roles'
    response = requests.get(url, headers=build_headers())
    roles = json.loads(response.text)
    for role in roles:
        if role["name"] == role_name:
            return role["publicId"]
    print(f"Unable to find role {role_name} : {response.status_code} - {response.text}")
    return None
