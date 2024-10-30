import json
import os
import urllib
import requests


# Build the http headers, authorised using the group service account token passed as a command line argument
def build_headers():
    headers = {
        'Content-Type': 'application/vnd.api+json',
        'Authorization': 'token {0}'.format(os.getenv('SNYK_TOKEN'))
    }
    return headers


# Retrieve all group(s) I belong to
def groups(api_ver, pagination):
    if pagination is None:
        url = 'https://api.snyk.io/rest/groups?version={0}~beta'.format(api_ver)
    else:
        url = 'https://api.snyk.io/rest/groups?version={0}~beta&starting_after={1}'.format(api_ver, pagination)

    response = requests.request("GET", url, headers=build_headers())
    if response.status_code != 200:
        print(response.text)
    return response.text


# Retrieve all orgs within the identified group
def group_orgs(api_ver, grp, pagination):
    if pagination is None:
        url = 'https://api.snyk.io/rest/groups/{0}/orgs?version={1}'.format(grp['id'], api_ver)
    else:
        url = 'https://api.snyk.io/rest/groups/{0}/orgs?version={1}&starting_after={2}'.format(grp['id'], api_ver,
                                                                                               pagination)
    response = requests.request("GET", url, headers=build_headers())
    if response.status_code != 200:
        print(response.text)
    return response.text


def get_collections(api_ver, org, pagination):

    if pagination is None:
        url = 'https://api.snyk.io/rest/orgs/{0}/collections?version={1}'.format(org['id'], api_ver)
    else:
        url = 'https://api.snyk.io/rest/orgs/{0}/collections?version={1}&starting_after={2}'.format(org['id'], api_ver, pagination)

    response = requests.request("GET", url, headers=build_headers())
    return response.text


def create_a_collection(args, org):
    name = '{0}'.format(args["collection_name"])
    body = {"data": {"attributes": {"name": name}, "type": "resource"}}

    # If it already exists, fail silently.
    url = 'https://api.snyk.io/rest/orgs/{0}/collections?version={1}'.format(org['id'], args["api_ver"])
    response = requests.post(url, json=body, headers=build_headers())

    if response.status_code == 201:
        # Newly created
        return json.loads(response.text)['data']['id']
    return None


def add_project_to_collection(args, org, collection_id, project):
    url = 'https://api.snyk.io/rest/orgs/{0}/collections/{1}/relationships/projects?version={2}'.format(org['id'],
                                                                                                        collection_id,
                                                                                                        args["api_ver"])
    body = {
        "data": [
            {
                "id": project["id"],
                "type": "project"
            }
        ]
    }
    response = requests.post(url, json=body, headers=build_headers())
    return response.text


def remove_collection(args, org, collection_id):
    url = 'https://api.snyk.io/rest/orgs/{0}/collections/{1}?version={2}'.format(org['id'], collection_id, args["api_ver"])
    response = requests.request("DELETE", url, headers=build_headers())
    return response.text


def org_projects(api_ver, org, project_tags, pagination):
    # project tags must be encoded
    if pagination is None:
        url = 'https://api.snyk.io/rest/orgs/{0}/projects?version={1}&tags={2}'.format(org['id'], api_ver,
                                                                                       urllib.parse.quote(
                                                                                           project_tags.replace(" ",
                                                                                                                "")))
    else:
        url = 'https://api.snyk.io/rest/orgs/{0}/projects?version={1}&tags={2}&starting_after={3}'.format(org['id'],
                                                                                                          api_ver,
                                                                                                          urllib.parse.quote(
                                                                                                              project_tags.replace(
                                                                                                                  " ",
                                                                                                                  "")),
                                                                                                          pagination)
    response = requests.request("GET", url, headers=build_headers())
    return response.text


def project_issues(api_ver, org, limit, proj_id, issue_type, effective_severity_level, pagination):
    if pagination is None:
        url = 'https://api.snyk.io/rest/orgs/{0}/issues?version={1}&limit={2}&scan_item.id={3}&scan_item.type={4}&effective_severity_level={5}'.format(
            org['id'], api_ver, limit, proj_id, issue_type, effective_severity_level.replace(" ", ""))
    else:
        url = 'https://api.snyk.io/rest/orgs/{0}/issues?version={1}&limit={2}&scan_item.id={3}&scan_item.type={4}&effective_severity_level={5}&starting_after={6}'.format(
            org['id'], api_ver, limit, proj_id, issue_type, effective_severity_level.replace(" ", ""), pagination)

    response = requests.request("GET", url, headers=build_headers())
    return response.text