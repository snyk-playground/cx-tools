import json
import os
import urllib
import requests
from urllib.parse import urlparse, unquote

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


# Create a named collection in a specified org
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


# Delete the collection from an org
def remove_collection(args, org, collection_id):
    url = f'{SNYK_REST_API_BASE_URL}/orgs/{org["id"]}/collections/{collection_id}?version={args["api_ver"]}'
    response = requests.request("DELETE", url, headers=build_headers())
    return response


# Retrieve projects from a given org that have a specific tag
def org_projects(org, pagination, project_tags=None):
    # project tags must be encoded
    if project_tags is None:
        if pagination is None:
            url = '{0}/orgs/{1}/projects?version={2}'.format(SNYK_REST_API_BASE_URL,
                                                             org['id'],
                                                             os.environ["API_VERSION"])
        else:
            url = '{0}/orgs/{1}/projects?version={2}&starting_after={3}'.format(SNYK_REST_API_BASE_URL,
                                                                                org['id'],
                                                                                os.environ["API_VERSION"],
                                                                                pagination)
    else:
        if pagination is None:
            url = '{0}/orgs/{1}/projects?version={2}&tags={3}'.format(SNYK_REST_API_BASE_URL,
                                                                      org['id'],
                                                                      os.environ["API_VERSION"],
                                                                      urllib.parse.quote(project_tags.replace(" ", "")))
        else:
            url = '{0}/orgs/{1}/projects?version={2}&tags={3}&starting_after={4}'.format(SNYK_REST_API_BASE_URL,
                                                                                         org['id'],
                                                                                         os.environ["API_VERSION"],
                                                                                         urllib.parse.quote(
                                                                                             project_tags.replace(" ",
                                                                                                                  "")),
                                                                                         pagination)
    response = requests.request("GET", url, headers=build_headers())
    return response


# Retrieve projects from a given org that have a specific tag
def org_projects(org, pagination):
    # project tags must be encoded
    if pagination is None:
        url = '{0}/orgs/{1}/projects?version={2}'.format(SNYK_REST_API_BASE_URL,
                                                         org['id'],
                                                         os.environ["API_VERSION"])
    else:
        url = '{0}/orgs/{1}/projects?version={2}&starting_after={3}'.format(SNYK_REST_API_BASE_URL,
                                                                            org['id'],
                                                                            os.environ["API_VERSION"],
                                                                            pagination)
    response = requests.request("GET", url, headers=build_headers())
    return response


# Retrieve org project issues of a specified severity level
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


# Function to parse all target for a known organisation
def org_targets(org_id, pagination):
    if pagination is None:
        url = f'{SNYK_REST_API_BASE_URL}/orgs/{org_id}/targets?version={os.environ["API_VERSION"]}'
    else:
        url = f'{SNYK_REST_API_BASE_URL}/orgs/{org_id}/targets?version={os.environ["API_VERSION"]}&starting_after={pagination}'

    response = requests.request("GET", url, headers=build_headers())
    return response


# Function to parse all target for a known organisation
def target_details(org_id, target_id):
    url = f'{SNYK_REST_API_BASE_URL}/orgs/{org_id}/targets/{target_id}?version={os.environ["API_VERSION"]}'
    response = requests.request("GET", url, headers=build_headers())
    return response


def export_group_data(args):
    url = f'{SNYK_REST_API_BASE_URL}/groups/{args["grp_id"]}/export?version={os.environ["API_VERSION"]}'
    payload = {
        "data": {
            "attributes": {
                "filters": {
                    "general": {
                        "orgs": args["orgs"]
                    },
                    "introduced": {
                        "from": args["introduced_from"],
                        "to": args["introduced_to"]
                    },
                    "updated": {
                        "from": args["updated_from"],
                        "to": args["updated_to"]
                    },
                    "projects": {
                        "environment": args["env"],
                        "lifecycle": args["lifecycle"]
                    }
                },
                "columns": args["columns"],
                "destination": {
                    "file_name": "test_export",
                    "type": "snyk"
                },
                "formats": [
                    "csv"
                ],
                "dataset": "issues"
            },
            "type": "resource"
        }
    }

    data = requests.post(url, json=payload, headers=build_headers())
    return data.text


def get_orgs_in_group(grp_id):
    url = f'{SNYK_REST_API_BASE_URL}/groups/{grp_id}/orgs?version={os.environ["API_VERSION"]}'
    response = requests.get(url, headers=build_headers())

    if response.status_code != 200:
        raise Exception(f"Failed to get orgs: {response.status_code} - {response.text}")

    orgs = response.json().get("data", [])
    return [org["id"] for org in orgs]


def export_status(grp_id, export_id):
    url = f'{SNYK_REST_API_BASE_URL}/groups/{grp_id}/jobs/export/{export_id}?version={os.environ["API_VERSION"]}'
    response = requests.get(url, headers=build_headers())
    return response.text


def download_report(args, export_id):
    # Get the report download url
    url = f'{SNYK_REST_API_BASE_URL}/groups/{args["grp_id"]}/export/{export_id}?version={os.environ["API_VERSION"]}'
    response = json.loads(requests.get(url, headers=build_headers()).text)
    # print(json.dumps(response, indent=4))

    with open(args["output_file"], "wb") as f:
        for result in response["data"]["attributes"]["results"]:
            url = unquote(result["url"])

            # Download the report from the url
            response = requests.get(url)
            if response.status_code == 200:
                f.write(response.content)
            else:
                print(f"❌ Failed to download data: {response.status_code}")
        print(f"✅ File downloaded successfully to {args['output_file']}")

    return response.status_code