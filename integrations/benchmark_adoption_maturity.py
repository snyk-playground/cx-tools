import argparse
import os

from integrations.utils.util_func import load_json_file, report_adoption_maturity


def get_arguments():
    parser = argparse.ArgumentParser(description='This script enables you to configure IQ Server from JSON\
     data, thus supporting the config-as-code requirement of Sonatype customers')
    parser.add_argument('-a', '--snyk_token', required=True)
    parser.add_argument('-c', '--config', required=True)
    parser.add_argument('-v', '--api_ver', required=True)
    parser.add_argument('-t', '--template', required=True)
    return vars(parser.parse_args())

# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    args = get_arguments()
    os.environ['SNYK_TOKEN'] = args['snyk_token']
    report_adoption_maturity(args)
