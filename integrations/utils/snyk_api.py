import json
import os
import requests


def build_headers():
    headers = {
        'Content-Type': 'application/json; charset=utf-8',
        'Authorization': 'token {0}'.format(os.getenv('SNYK_TOKEN'))
    }
    return headers


def org_integrations(org_id):
    response = None
    url = 'https://api.snyk.io/v1/org/{0}/integrations'.format(org_id)
    response = requests.request("GET", url, headers=build_headers())
    if response.status_code != 200:
        print(response.text)
    return response.text


def get_org_integration_settings(org_id, integration_id):
    response = None
    url = 'https://api.snyk.io/v1/org/{0}/integrations/{1}/settings'.format(org_id, integration_id)
    response = requests.request("GET", url, headers=build_headers())
    if response.status_code != 200:
        print(response.text)
    return response.text


# Update the config settings for a specified org and integration id
def update_org_integration_settings(org_id, integration_id, values):
    response = None
    url = 'https://api.snyk.io/v1/org/{0}/integrations/{1}/settings'.format(org_id, integration_id)
    response = requests.put(url, headers=build_headers(), json=values)
    if response.status_code != 200:
        print(response.text)
    return response.text
