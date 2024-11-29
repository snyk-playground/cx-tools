import json
import os
import urllib
import requests

SNYK_REST_API_BASE_URL = "https://api.snyk.io/rest"


# Build the http headers, authorised using the group service account token passed as a command line argument
def build_headers():
    headers = {
        'Content-Type': 'application/vnd.api+json',
        'Authorization': 'token {0}'.format(os.getenv('SNYK_TOKEN'))
    }
    return headers


# Retrieve all group(s) I belong to
def groups(pagination):
    if pagination is None:
        url = f'{SNYK_REST_API_BASE_URL}/groups?version={os.environ["API_VERSION"]}~beta'
    else:
        url = f'{SNYK_REST_API_BASE_URL}/groups?version={os.environ["API_VERSION"]}~beta&starting_after={pagination}'

    response = requests.request("GET", url, headers=build_headers())
    if response.status_code != 200:
        print(response.text)
    return response


# Retrieve all orgs within the identified group
def group_orgs(group, pagination):
    if pagination is None:
        url = f'{SNYK_REST_API_BASE_URL}/groups/{group["id"]}/orgs?version={os.environ["API_VERSION"]}'
    else:
        url = f'{SNYK_REST_API_BASE_URL}/groups/{group["id"]}/orgs?version={os.environ["API_VERSION"]}&starting_after={pagination}'
    response = requests.request("GET", url, headers=build_headers())
    if response.status_code != 200:
        print(response.text)
    return response


# Retrieve all the collections within the org
def get_collections(org, pagination):

    if pagination is None:
        url = f'{SNYK_REST_API_BASE_URL}/orgs/{org["id"]}/collections?version={os.environ["API_VERSION"]}'
    else:
        url = f'{SNYK_REST_API_BASE_URL}/orgs/{org["id"]}/collections?version={os.environ["API_VERSION"]}&starting_after={pagination}'

    response = requests.request("GET", url, headers=build_headers())
    return response


# Retrieve the specified collection contents
def get_collection(org, collection_id):

    url = f'{SNYK_REST_API_BASE_URL}/orgs/{org["id"]}/collections/{collection_id}?version={os.environ["API_VERSION"]}'

    response = requests.request("GET", url, headers=build_headers())
    return response


# Retrieve the projects within the specified collection
def get_collection_projects(org_id, collection_id, pagination):

    if pagination is None:
        url = f'{SNYK_REST_API_BASE_URL}/orgs/{org_id}/collections/{collection_id}/relationships/projects?version={os.environ["API_VERSION"]}'
    else:
        url = f'{SNYK_REST_API_BASE_URL}/orgs/{org_id}/collections/{collection_id}/relationships/projects?version={os.environ["API_VERSION"]}&starting_after={pagination}'

    response = requests.request("GET", url, headers=build_headers())
    return response


# Create a named collection
def create_a_collection(args, org):
    name = '{0}'.format(args["collection_name"])
    body = {"data": {"attributes": {"name": name}, "type": "resource"}}

    # If it already exists, fail silently.
    url = f'{SNYK_REST_API_BASE_URL}/orgs/{org["id"]}/collections?version={args["api_ver"]}'
    response = requests.post(url, json=body, headers=build_headers())

    if response.status_code == 201:
        # Newly created
        return json.loads(response.text)['data']['id']
    return None


# Add a project to an existing collection
def add_project_to_collection(org, collection_id, project_id):
    url = f'{SNYK_REST_API_BASE_URL}/orgs/{org["id"]}/collections/{collection_id}/relationships/projects?version={os.environ["API_VERSION"]}'
    body = {
        "data": [
            {
                "id": project_id,
                "type": "project"
            }
        ]
    }
    response = requests.post(url, json=body, headers=build_headers())
    return response


# Delete a project from an existing collection
def delete_project_from_collection(org, collection_id, project_id):
    url = f'{SNYK_REST_API_BASE_URL}/orgs/{org["id"]}/collections/{collection_id}/relationships/projects?version={os.environ["API_VERSION"]}'
    body = {
        "data": [
            {
                "id": project_id,
                "type": "project"
            }
        ]
    }
    response = requests.delete(url, json=body, headers=build_headers())
    return response


def remove_collection(args, org, collection_id):
    url = f'{SNYK_REST_API_BASE_URL}/orgs/{org["id"]}/collections/{collection_id}?version={args["api_ver"]}'
    response = requests.request("DELETE", url, headers=build_headers())
    return response


def org_projects(org, project_tags, pagination):
    # project tags must be encoded
    if pagination is None:
        url = 'https://api.snyk.io/rest/orgs/{0}/projects?version={1}&tags={2}'.format(org['id'],
                                                                                       os.environ["API_VERSION"],
                                                                                       urllib.parse.quote(
                                                                                           project_tags.replace(" ",
                                                                                                                "")))
    else:
        url = 'https://api.snyk.io/rest/orgs/{0}/projects?version={1}&tags={2}&starting_after={3}'.format(org['id'],
                                                                                                          os.environ["API_VERSION"],
                                                                                                          urllib.parse.quote(
                                                                                                              project_tags.replace(
                                                                                                                  " ",
                                                                                                                  "")),
                                                                                                          pagination)
    response = requests.request("GET", url, headers=build_headers())
    return response


def project_issues(org, limit, proj_id, issue_type, effective_severity_level, pagination):
    if pagination is None:
        url = f'{SNYK_REST_API_BASE_URL}/orgs/{org["id"]}/issues?version={os.environ["API_VERSION"]}&limit={limit}&scan_item.id={proj_id}&scan_item.type={issue_type}&effective_severity_level={effective_severity_level.replace(" ", "")}'
    else:
        url = f'{SNYK_REST_API_BASE_URL}/orgs/{org["id"]}/issues?version={os.environ["API_VERSION"]}&limit={limit}&scan_item.id={proj_id}&scan_item.type={issue_type}&effective_severity_level={effective_severity_level.replace(" ", "")}&starting_after={pagination}'

    response = requests.request("GET", url, headers=build_headers())
    return response


# Create the service account within the target org and return the auth-key post creation only
def create_service_account(org_id, role_id, svc_ac_name):
    url = f'{SNYK_REST_API_BASE_URL}/orgs/{org_id}/service_accounts?version={os.environ["API_VERSION"]}'
    payload = {
        "data": {
            "attributes": {
                "auth_type": "api_key",
                "name": "{0}".format(svc_ac_name),
                "role_id": "{0}".format(role_id)
            },
            "type": "service_account"
        }
    }

    # Make the POST request to create the service account
    return requests.post(url, json=payload, headers=build_headers())
