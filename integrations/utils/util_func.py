import json
import urllib.parse
import jsoncomparison

from integrations.utils.rest_api import group_orgs
from integrations.utils.rest_api import groups
from integrations.utils.snyk_api import org_integrations, update_org_integration_settings
from integrations.utils.snyk_api import get_org_integration_settings

CFG_DELIMETER = "::"

# Handle pagination
def next_page(response):
    # response['links']['next']
    try:
        pagination = urllib.parse.parse_qs(response['links']['next'],
                                           keep_blank_values=False, strict_parsing=False,
                                           encoding='utf-8', errors='replace',
                                           max_num_fields=None, separator='&')
        pagination = pagination['starting_after'][0]
    except:
        pagination = None
    return pagination


# Is the current org in scope?
def org_of_interest(orgs, orgname):
    if orgs == None or orgname in orgs:
        return True
    return False


# Parse all the integrations for a group/specific orgs of interest to a file
def parse_integrations(args):
    orgs_integrations = dict()
    g_response = None

    try:
        g_pagination = None
        while True:
            # Retrieve all my groups
            g_response = json.loads(groups(args["api_ver"], g_pagination))

            go_response = None
            try:
                # Iterate to the named group
                for group in g_response['data']:
                    if group['attributes']['name'] == args['grp_name']:
                        go_pagination = None
                        while True:
                            go_response = json.loads(group_orgs(args["api_ver"], group, go_pagination))

                            # Iterate to the named Org
                            for org in go_response['data']:
                                if org_of_interest(args["org_names"], org['attributes']['name']):

                                    # Parse the integrations
                                    org_ints_response = json.loads(org_integrations(org['id']))
                                    orgs_integrations[org["attributes"]["name"]+CFG_DELIMETER+org["id"]] = {}

                                    # Collate the integration settings by name within the org
                                    for org_int in org_ints_response:
                                        settings = json.loads(get_org_integration_settings(org['id'], org_ints_response[org_int]))
                                        orgs_integrations[org['attributes']['name']+CFG_DELIMETER+org["id"]] \
                                            [org_int+CFG_DELIMETER+org_ints_response[org_int]] = settings

                            # Next page?
                            go_pagination = next_page(go_response)
                            if go_pagination is None:
                                break

            except UnboundLocalError as err:
                print(err)
                print("GET call to /orgs API returned no 'data'")
                print(json.dumps(go_response, indent=4))
            except TypeError as err:
                print(err)

            # Next page?
            g_pagination = next_page(g_response)
            if g_pagination is None:
                break
    except UnboundLocalError as err:
        print(err)
        print("GET call to /groups API returned no 'data'")
        print(json.dumps(g_response, indent=4))
    finally:
        return orgs_integrations


# Update the integrations with the config persisted in a file
def update_integrations(args):
    my_config = args["config_file"]
    orgs = load_json_file(my_config)
    print(f"Upload data parsed from {my_config}")

    for org in orgs:
        org_id = org.split(CFG_DELIMETER)[1]
        for integration in orgs[org]:
            integration_id = integration.split(CFG_DELIMETER)[1]
            update_org_integration_settings(org_id, integration_id, orgs[org][integration])


# Utility fundtion to load json object from a file
def load_json_file(filename):
    try:
        f = open(filename)
        orgs = json.load(f)
        return orgs
    except FileNotFoundError as err:
        print(err)
        return None


def report_adoption_maturity(args):
    orgs = load_json_file(args["config"])
    template_file = args['template']
    templates = load_json_file(f"{template_file}")

    for org in orgs:
        integrations = orgs[org]
        for name in integrations:
            integration = integrations[name]
            template_name = name.split(CFG_DELIMETER)[0]
            try:
                template = templates[template_name]
                diff = jsoncomparison.Compare().check(template, integration)
                if len(diff):
                    print(f"Organisation {org.split(CFG_DELIMETER)[0]} - {template_name} integration configuration benchmark results against {template_file}")
                    print(json.dumps(diff, indent=4))
                else:
                    print(f"Organisation {org.split(CFG_DELIMETER)[0]} - {template_name} integration configuration is aligned with {template_file}")

            except KeyError as err:
                print(f"Organisation {org.split(CFG_DELIMETER)[0]} {err} integration. Template configuration does not exist in {template_file}")
