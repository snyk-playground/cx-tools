import argparse
import os
import json

from integrations.utils.util_func import parse_integrations


def get_arguments():
    parser = argparse.ArgumentParser(description='This script enables you to configure IQ Server from JSON\
     data, thus supporting the config-as-code requirement of Sonatype customers')
    parser.add_argument('-a', '--snyk_token', required=True)
    parser.add_argument('-g', '--grp_name', required=True)
    parser.add_argument('-v', '--api_ver', required=True)
    parser.add_argument('-o', '--org_names', default=None)

    args = vars(parser.parse_args())
    if args["org_names"] is not None:
        args["org_names"] = args["org_names"].split(',')
        index = 0
        for org_name in args["org_names"]:
            args["org_names"][index] = (org_name.strip())
            index += 1
    return args


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    args = get_arguments()
    os.environ['SNYK_TOKEN'] = args['snyk_token']
    integrations = parse_integrations(args)
    if args["org_names"] is None:
        filename = os.getcwd() + "/" + args["grp_name"] + "_Snyk_Integrations.json"
    else:
        filename = os.getcwd() + "/" + args["grp_name"] + "--" + ''.join(args["org_names"]) + "_Snyk_Integrations.json"

    with open(filename, "w") as outfile:
        json.dump(integrations, outfile, indent=4)
        print(f"Results written to {filename}")
