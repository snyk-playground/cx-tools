import json
import urllib.parse

from integrations.utils.rest_api import group_orgs
from integrations.utils.rest_api import groups
from integrations.utils.snyk_api import org_integrations
from integrations.utils.snyk_api import get_org_integration_settings

CFG_DELIMETER = "::"

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

def org_of_interest(orgs, orgname):
    if orgs == None or orgname in orgs:
        return True
    return False



# Parse all the integrations for orgs of interest to a group scoped file
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


def update_integrations(args):
    orgs = {}
    g_response = None

    #try:
    name = "/Users/kevinmatthews/cx-tools/integrations/"+args["grp_name"]+"_integrations.json"
    f = open(name)
    orgs = json.load(f)

    for org in orgs:
        print(org)
        print(json.dumps(orgs[org], indent=4))
        for integration in orgs[org]:
            print(json.dumps(integration, indent=4))
    #finally:
        #print(json.dumps(orgs_integrations, indent=4))
    #    return
