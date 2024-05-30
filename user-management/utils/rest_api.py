import json
import urllib.parse
import requests


# Retrieve all group I belong to
def groups(headers, api_ver):
    url = 'https://api.snyk.io/rest/groups?version={0}~beta'.format(api_ver)
    return requests.request("GET", url, headers=headers).text


# Retrieve all orgs within the identified group
def group_orgs(headers, api_ver, grp, pagination):
    if pagination is None:
        url = 'https://api.snyk.io/rest/groups/{0}/orgs?version={1}~beta'.format(grp['id'], api_ver)
    else:
        url = 'https://api.snyk.io/rest/groups/{0}/orgs?version={1}&starting_after={2}'.format(grp['id'], api_ver,
                                                                                               pagination)
    response = requests.request("GET", url, headers=headers)
    return response.text


