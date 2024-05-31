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
    parser.add_argument('-o', '--org_names', default=None)
    parser.add_argument('-r', '--roles', required=True)
    parser.add_argument('-v', '--api_ver', default="2024-05-23")


    args = vars(parser.parse_args())
    if args["roles"] != None:
        args["roles"]=args["roles"].replace(" ","").split(',')
    if args["org_names"] != None:
        args["org_names"]=args["org_names"].replace(" ","").split(',')
    return args


# Press the green button in the gutter to run the script.
if __name__ == '__main__':

    args = get_arguments()
    os.environ['SNYK_TOKEN'] = args['snyk_token']

    headers = {
      'Content-Type': 'application/vnd.api+json',
      'Authorization': 'token {0}'.format(os.getenv('SNYK_TOKEN'))
    }

    utils.util_func.parse_users(headers, args)


