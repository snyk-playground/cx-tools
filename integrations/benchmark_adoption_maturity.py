import argparse
import os

from integrations.utils.util_func import report_adoption_maturity


def get_arguments():
    parser = argparse.ArgumentParser(description='This script enables you to benchmark persisted SCM configuration'
                                                 'data against a known baseline configuration to identify disparity'
                                                 'with such baseline. Snyk customers can use this to understand their '
                                                 'SDLC controls and effect configured appetite to risk.')
    parser.add_argument('-a', '--snyk_token', default=None)
    parser.add_argument('-c', '--config', required=True)
    parser.add_argument('-v', '--api_ver', default="2024-08-15")
    parser.add_argument('-t', '--template', required=True)
    args = vars(parser.parse_args())
    if args["snyk_token"]:
        os.environ["SNYK_TOKEN"] = args["snyk_token"]
    os.environ["API_VERSION"] = args["api_ver"]

    return args

# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    args = get_arguments()
    report_adoption_maturity(args)
