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
    parser.add_argument('-o', '--org_names', required=True, default=None)
    # parser.add_argument('-s', '--scope', required=True)
    parser.add_argument('-v', '--api_ver', default="2024-01-23")


    args = vars(parser.parse_args())
    args["org_names"]=args["org_names"].split(',')
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


# Press the green button in the gutter to run the script.
if __name__ == '__main__':

    args = get_arguments()
    os.environ['SNYK_TOKEN'] = args['snyk_token']

    headers = {
      'Content-Type': 'application/vnd.api+json',
      'Authorization': 'token {0}'.format(os.getenv('SNYK_TOKEN'))
    }

    utils.util_func.parse_users(headers, args)


