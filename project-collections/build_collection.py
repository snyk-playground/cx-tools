import argparse
import json
import os
import urllib

import utils.util_func


def get_arguments():
    parser = argparse.ArgumentParser(description='This script enables you to configure IQ Server from JSON\
     data, thus supporting the config-as-code requirement of Sonatype customers')
    parser.add_argument('-a', '--snyk_token', required=True)
    parser.add_argument('-g', '--grp_name', required=True)
    parser.add_argument('-o', '--org_name', required=True)
    parser.add_argument('-c', '--collection_name', required=True)
    parser.add_argument('-t', '--project_tags', required=True)
    parser.add_argument('-v', '--api_ver', default="2024-01-23")

    args = vars(parser.parse_args())
    return args


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


def add_proj_to_collection(headers, args, org, collection_id):
    op_pagination = None
    while True:
        # Use of the project_tags ensures only those with the right tag are returned
        op_response = json.loads(
            utils.rest_api.org_projects(headers, args["api_ver"], org,
                                        args["project_tags"], op_pagination))

        for project in op_response['data']:
            # iterate over the tags in each project and persist it i it has one of the tags
            # of interest
            utils.rest_api.add_project_to_collection(headers, args, org, collection_id, project)

        # Next page?
        op_pagination = next_page(op_response)
        if op_pagination is None:
            break




# Press the green button in the gutter to run the script.
if __name__ == '__main__':

    args = get_arguments()
    os.environ['SNYK_TOKEN'] = args['snyk_token']

    headers = {
      'Content-Type': 'application/vnd.api+json',
      'Authorization': 'token {0}'.format(os.getenv('SNYK_TOKEN'))
    }

    utils.util_func.process_collection(headers, args, add_proj_to_collection)


