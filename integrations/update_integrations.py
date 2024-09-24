import argparse
import os
import utils.util_func
from integrations.utils.util_func import update_integrations

def get_arguments():
    parser = argparse.ArgumentParser(description='Script to update Snyk integration settings')
    parser.add_argument('-a', '--snyk_token', required=True)
    parser.add_argument('-c', '--config', required=True)
    parser.add_argument('-v', '--api_ver', required=True)
    parser.add_argument('-t', '--template', default=None)
    args = vars(parser.parse_args())
    return args

# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    args = get_arguments()
    os.environ['SNYK_TOKEN'] = args['snyk_token']
    update_integrations(args)


