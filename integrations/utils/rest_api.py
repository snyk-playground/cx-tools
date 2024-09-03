import os
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

    return requests.request("GET", url, headers=build_headers()).text


# Retrieve all orgs within the identified group
def group_orgs(api_ver, grp, pagination):
    if pagination is None:
        url = 'https://api.snyk.io/rest/groups/{0}/orgs?version={1}'.format(grp['id'], api_ver)
    else:
        url = 'https://api.snyk.io/rest/groups/{0}/orgs?version={1}&starting_after={2}'.format(grp['id'], api_ver,
                                                                                               pagination)
    response = requests.request("GET", url, headers=build_headers())
    return response.text


