import json
import jsoncomparison

from apis.pagination import next_page
from apis.rest_api import groups, group_orgs
from apis.snyk_api import org_integrations, get_org_integration_settings, update_org_integration_settings

CFG_DELIMITER = "::"

# Handle pagination
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
                                    orgs_integrations[org["attributes"]["name"] + CFG_DELIMITER + org["id"]] = {}

                                    # Collate the integration settings by name within the org
                                    for org_int in org_ints_response:
                                        settings = json.loads(get_org_integration_settings(org['id'], org_ints_response[org_int]))
                                        orgs_integrations[org['attributes']['name'] + CFG_DELIMITER + org["id"]] \
                                            [org_int + CFG_DELIMITER + org_ints_response[org_int]] = settings

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
    try:
        my_config = args["config"]
        orgs = load_json_file(my_config)
        print(f"Organisation data parsed from {my_config}")
        template = None

        if args["template"] is not None:
            template = load_json_file(args["template"])
            my_config = args["template"]

        for org in orgs:
            org_name = org.split(CFG_DELIMITER)[0]
            org_id = org.split(CFG_DELIMITER)[1]

            # Iterate over the orgs, identify the config data and apply it
            for integration in orgs[org]:
                try:
                    integration_name = integration.split(CFG_DELIMITER)[0]
                    integration_id = integration.split(CFG_DELIMITER)[1]
                    config_to_apply = None

                    # Retrieve the integration config data to be applied from the template
                    # or the persisted org config data
                    if template:
                        config_to_apply = template[integration_name]
                    else:
                        config_to_apply = orgs[org][integration]

                    #  Not every integration has data returned and persisted
                    if len(config_to_apply):
                        update_org_integration_settings(org_id, integration_id, config_to_apply)
                        print(f"{integration_name} configuration was applied from '{my_config}' to the {org_name} organisation")
                except KeyError:
                    # The templates don't contain empty data for integrations whose config is not returned
                    # by the api and persisted.
                    pass

    except FileNotFoundError as err:
        print(err)


# Utility function to load json object from a file
def load_json_file(filename):
    f = open(filename)
    data = json.load(f)
    return data


# Function to parse the persisted config, benchmark it against the chosen template and report the differences
def report_adoption_maturity(args):
    try:
        orgs = load_json_file(args["config"])
        template_file = args['template']
        templates = load_json_file(f"{template_file}")

        for org in orgs:
            integrations = orgs[org]
            for name in integrations:
                integration = integrations[name]
                template_name = name.split(CFG_DELIMITER)[0]
                try:
                    template = templates[template_name]
                    diff = jsoncomparison.Compare().check(template, integration)
                    if len(diff):
                        print(f"Organisation {org.split(CFG_DELIMITER)[0]} - {template_name} integration configuration benchmark results against {template_file}")
                        print(json.dumps(diff, indent=4))
                    else:
                        print(f"Organisation {org.split(CFG_DELIMITER)[0]} - {template_name} integration configuration is aligned with {template_file}")

                except KeyError as err:
                    print(f"Organisation {org.split(CFG_DELIMITER)[0]} {err} integration. Template configuration does not exist in {template_file}")
    except FileNotFoundError as err:
        print(err)
