import argparse
import os
from utils.util_func import parse_users


def get_arguments():
    parser = argparse.ArgumentParser(description='This script enables you to configure IQ Server from JSON\
     data, thus supporting the config-as-code requirement of Sonatype customers')
    parser.add_argument('-a', '--snyk_token', default=None)
    parser.add_argument('-g', '--grp_name', required=True)
    parser.add_argument('-o', '--org_names', default=None)
    parser.add_argument('-r', '--roles', required=True)
    parser.add_argument('-v', '--api_ver', default="2024-08-15")

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


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    args = get_arguments()
    parse_users(args)
