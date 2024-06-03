import json
import requests


def org_integrations(headers, org_id):
    response = None
    try:
        url = 'https://api.snyk.io/v1/org/{0}/integrations'.format(org_id)
        response = requests.request("GET", url, headers=headers).text
        return response
    except Exception:
        print(json.dumps(response, indent=4))


def org_int_settings(headers, org_id, integration_id):
    response = None
    try:
        url = 'https://api.snyk.io/v1/org/{0}/integrations/{1}/settings'.format(org_id, integration_id)
        response = requests.request("GET", url, headers=headers).text
        return response
    except Exception:
        print(json.dumps(response, indent=4))