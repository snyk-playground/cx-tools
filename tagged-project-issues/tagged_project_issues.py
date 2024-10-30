import argparse
import os
from utils.util_func import tagged_project_issues

def get_arguments():
    parser = argparse.ArgumentParser(description='This script enables you to configure IQ Server from JSON\
     data, thus supporting the config-as-code requirement of Sonatype customers')
    parser.add_argument('-a', '--snyk_token', default=None)
    parser.add_argument('-g', '--grp_name', required=True)
    parser.add_argument('-o', '--org_name', required=True)
    parser.add_argument('-t', '--project_tags', required=True)
    parser.add_argument('-v', '--api_ver', default="2024-01-23")
    parser.add_argument('-s', '--effective_severity_level', default="critical,high")

    args = vars(parser.parse_args())
    if args["snyk_token"]:
        os.environ["SNYK_TOKEN"] = args["snyk_token"]
    return args

# Press the green button in the gutter to run the script.
if __name__ == '__main__':

    args = get_arguments()

    headers = {
      'Content-Type': 'application/vnd.api+json',
      'Authorization': 'token {0}'.format(os.getenv('SNYK_TOKEN'))
    }

    tagged_project_issues(headers, args)