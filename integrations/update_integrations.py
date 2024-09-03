import argparse
import os
import utils.util_func


def get_arguments():
    parser = argparse.ArgumentParser(description='Script to update Snyk integration settings')
    parser.add_argument('-a', '--snyk_token', required=True)
    parser.add_argument('-c', '--config_file', required=True)
    parser.add_argument('-v', '--api_ver', required=True)
    args = vars(parser.parse_args())
    return args

# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    args = get_arguments()
    os.environ['SNYK_TOKEN'] = args['snyk_token']
    utils.util_func.update_integrations(args)


