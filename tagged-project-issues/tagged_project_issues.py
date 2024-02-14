import argparse
import json
import os
import utils.util_func


def get_arguments():
    parser = argparse.ArgumentParser(description='This script enables you to configure IQ Server from JSON\
     data, thus supporting the config-as-code requirement of Sonatype customers')
    parser.add_argument('-a', '--snyk_token', required=True)
    parser.add_argument('-g', '--grp_name', required=True)
    parser.add_argument('-o', '--org_name', required=True)
    parser.add_argument('-t', '--project_tags', required=True)
    parser.add_argument('-v', '--api_ver', default="2024-01-23")
    parser.add_argument('-s', '--effective_severity_level', default="critical,high")

    args = vars(parser.parse_args())
    return args

# Press the green button in the gutter to run the script.
if __name__ == '__main__':

    args = get_arguments()
    os.environ['SNYK_TOKEN'] = args['snyk_token']

    headers = {
      'Content-Type': 'application/json',
      'Authorization': 'token {0}'.format(os.getenv('SNYK_TOKEN'))
    }

    utils.util_func.tagged_project_issues(headers, args)