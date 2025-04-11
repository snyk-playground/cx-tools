import argparse
import os
import json

from apis.pagination import next_page
from apis.rest_api import groups, group_orgs, org_targets, target_details, org_projects


def get_arguments():
    parser = argparse.ArgumentParser(description='This script enables you to persist SCM integration data for all/some '
                                                 'orgs within a Snyk group.')
    parser.add_argument('-a', '--snyk_token', default=None)
    parser.add_argument('-g', '--grp_name', required=True)
    parser.add_argument('-v', '--api_ver', default="2024-08-15")
    parser.add_argument('-o', '--org_names', default=None)

    args = vars(parser.parse_args())
    if args["snyk_token"]:
        os.environ["SNYK_TOKEN"] = args["snyk_token"]

    if args["org_names"] is not None:
        args["org_names"] = args["org_names"].split(',')
        index = 0
        for org_name in args["org_names"]:
            args["org_names"][index] = (org_name.strip())
            index += 1

    os.environ["API_VERSION"] = args["api_ver"]
    return args

# Handle pagination
# Is the current org in scope?
def org_of_interest(orgs, orgname):
    if orgs == None or orgname in orgs:
        return True
    return False


# Parse all the targets for a group/specific orgs of interest to a file
def reconcile_targets(args):
    grp_targets = dict()
    g_response = None

    try:
        g_pagination = None
        while True:
            # Retrieve all my groups
            g_response = json.loads(groups(g_pagination).text)

            go_response = None
            try:
                # Iterate to the named group
                for group in g_response['data']:
                    if group['attributes']['name'] == args['grp_name']:
                        go_pagination = None
                        while True:
                            go_response = json.loads(group_orgs(group, go_pagination).text)

                            # Iterate to the named Org
                            for org in go_response['data']:
                                target_pagination = None
                                if org_of_interest(args["org_names"], org['attributes']['name']):
                                    grp_targets[org['attributes']['name']] = list()
                                    data = dict()

                                    # Parse the targets
                                    while True:
                                        targets = json.loads(org_targets(org['id'], target_pagination).text)

                                        # Iterate over the targets in the org
                                        for target in targets['data']:
                                            # Load the target details
                                            target_data = json.loads(target_details(org['id'], target['id']).text)
                                            # print(target_data)
                                            # Create a dict of target attributes
                                            data[target_data['data']['id']] = dict()
                                            # Cache the target attributes
                                            target_attrs = data[target_data['data']['id']]
                                            target_attrs['url'] = (target_data['data']['attributes']['url'])
                                            target_attrs["integration_type"] = target_data['data']['relationships']\
                                                ['integration']['data']['attributes']['integration_type']
                                            target_attrs['display_name'] = target_data['data']['attributes']\
                                                ['display_name']
                                            # Create the placeholder list for the projects within the target that will
                                            # be x-ref and cached later
                                            target_attrs['projects'] = list()

                                        # Next page?
                                        target_pagination = next_page(targets)
                                        if target_pagination is None:
                                            break

                                    grp_targets[org['attributes']['name']].append(data)

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
        return grp_targets

def xref_target_projects(grp_targets):
    g_response = None

    try:
        g_pagination = None
        while True:
            # Retrieve all my groups
            g_response = json.loads(groups(g_pagination).text)

            go_response = None
            try:
                # Iterate to the named group
                for group in g_response['data']:
                    if group['attributes']['name'] == args['grp_name']:
                        go_pagination = None
                        while True:
                            go_response = json.loads(group_orgs(group, go_pagination).text)

                            # Iterate to the named Org
                            for org in go_response['data']:
                                if org_of_interest(args["org_names"], org['attributes']['name']):

                                    # Find the list of target refs for this org
                                    org_targets = None
                                    for name, list in grp_targets.items():
                                        if name == org["attributes"]["name"]:
                                            # Reference the targets list for the current organisation
                                            org_targets = list
                                            break

                                    # Parse the projects
                                    project_pagination = None
                                    while True:
                                        # Load the next page of projects for the org
                                        projects = json.loads(org_projects(org, project_pagination).text)

                                        for project in projects['data']:
                                            # Find the target id for this project
                                            target_id  = project["relationships"]["target"]["data"]["id"]
                                            # Find the target data in the list of targets for this org
                                            target_data = [d for d in org_targets if target_id in d]
                                            # Index the projects list in the cached target
                                            target_projects = target_data[0][target_id]['projects']
                                            # Append the dict for the project attributes
                                            target_projects.append(dict())
                                            index = len(target_projects)-1
                                            # Add the project attributes to the dictionary for this project, within the
                                            # list or projects for the target
                                            target_projects[index]['name'] = project["attributes"]["name"]
                                            target_projects[index]['id'] = project["id"]
                                            target_projects[index]['type'] = project["attributes"]["type"]
                                            target_projects[index]['origin'] = project["attributes"]["origin"]
                                            target_projects[index]['target_file'] = project["attributes"]["target_file"]
                                            target_projects[index]['target_reference'] = project["attributes"]["target_reference"]
                                            # print(target_data)

                                        # Next page?
                                        project_pagination = next_page(projects)
                                        if project_pagination is None:
                                            break
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
        return grp_targets


if __name__ == '__main__':
    args = get_arguments()
    targets = reconcile_targets(args)

    if args["org_names"] is None:
        filename = os.getcwd() + "/" + args["grp_name"] + "_Targets.json"
    else:
        filename = os.getcwd() + "/" + args["grp_name"] + "--" + ''.join(args["org_names"]) + "_Targets.json"

    targets = xref_target_projects(targets)

    with open(filename, "w") as outfile:
        json.dump(targets, outfile, indent=4)
        print(f"Results written to {filename}")
