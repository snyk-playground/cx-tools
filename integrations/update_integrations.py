import argparse
import os

from integrations.utils.util_func import update_integrations


def get_arguments():
    parser = argparse.ArgumentParser(description='This script enables users to configure SCM integration data, thus '
                                                 'ensuring Snyk customers can deploy security controls across the SDLC '
                                                 '(at scale) aligned with their risk appetite.')
    parser.add_argument('-a', '--snyk_token', default=None)
    parser.add_argument('-c', '--config', required=True)
    parser.add_argument('-v', '--api_ver', default="2024-08-15")
    parser.add_argument('-t', '--template', default=None)
    args = vars(parser.parse_args())
    if args["snyk_token"]:
        os.environ["SNYK_TOKEN"] = args["snyk_token"]

    os.environ["API_VERSION"] = args["api_ver"]
    return args

# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    args = get_arguments()
    update_integrations(args)


