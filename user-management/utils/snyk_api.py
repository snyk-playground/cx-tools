import requests


def org_members(headers, org_id):
    url = 'https://api.snyk.io/v1/org/{0}/members?includeGroupAdmins=true'.format(org_id)
    return requests.request("GET", url, headers=headers).text
