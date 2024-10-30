import json
from apis.pagination import next_page
from apis.rest_api import group_orgs, org_projects, project_issues, groups


def tagged_project_issues(args):
    # Retrieve all my groups
    g_response = json.loads(groups(args["api_ver"], None))

    # dictionary for all the issues within the tagged projects
    tp_issues = {}

    # Parse the list of tag values that identify projects of interest
    projects_of_interest = []
    tag_values = []
    tags = args["project_tags"].split(",")
    for tag in tags:
        tag_values.append(tag)

    # Iterate to the named group
    for group in g_response['data']:
        if group['attributes']['name'] == args['grp_name']:
            go_pagination = None
            while True:
                go_response = json.loads(group_orgs(args["api_ver"], group, go_pagination))

                # Iterate to the named Org
                for org in go_response['data']:
                    if org['attributes']['name'] == args["org_name"]:

                        op_pagination = None
                        while True:
                            # Use of the project_tags ensures only those with the right tag are returned
                            op_response = json.loads(
                                org_projects(args["api_ver"], org, args["project_tags"], op_pagination))

                            for project in op_response['data']:
                                # iterate over the tags in each project and persist it i it has one of the tags
                                # of interest
                                for tag in project['attributes']['tags']:
                                    if tagged_project_in_scope(tags, tag_values):
                                        # Ensure we don't pull the project issues twice if it contains multiple
                                        # tags of interest
                                        if not project in projects_of_interest:
                                            projects_of_interest.append(project)

                            # Next page?
                            op_pagination = next_page(op_response)
                            if op_pagination is None:
                                break

                # Next page?
                go_pagination = next_page(go_response)
                if go_pagination is None:
                    break


    # Iterate over the list o projects that comprise the tags of interest
    tagged_projects_with_issues = {}
    while len(projects_of_interest):
        pi_pagination = None
        project = projects_of_interest[0]

        while True:
            # Grab a page of vuln data for the current project
            pi_response = json.loads(
                project_issues(args["api_ver"],
                               project['relationships']['organization']['data'], '100', project['id'],
                               'project', args["effective_severity_level"], pi_pagination))

            # Print the project vuln page content
            if len(pi_response['data']):
                proj_issues = {}
                try:
                    project["issues"] =  project["issues"] + pi_response['data']
                except:
                    project["issues"] = pi_response['data']

                # project issues pagination - Next page?
                pi_pagination = next_page(pi_response)
                if pi_pagination is None:
                    break

            else:
                break

        # Inorder to not restart the 'for' loop, the project that has been processed
        # must be removed rom the list of interesting projects.
        projects_of_interest.remove(project)
        tagged_projects_with_issues[project["attributes"]["name"]] = (project)

    print(json.dumps(tagged_projects_with_issues, indent=4))


def tagged_project_in_scope(tags_in_scope, proj_tags):
    for tag in proj_tags:
        if tag in tags_in_scope:
            # tags_in_scope.remove(tag)
            return True
    return False
