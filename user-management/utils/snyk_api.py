import json
import requests


def org_members(headers, org_id):
    response = None
    try:
        url = 'https://api.snyk.io/v1/org/{0}/members?includeGroupAdmins=true'.format(org_id)
        response = requests.request("GET", url, headers=headers).text
        return response
    except Exception:
        print(json.dumps(response, indent=4))