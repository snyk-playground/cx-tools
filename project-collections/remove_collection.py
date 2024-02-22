import argparse
import os
import utils.util_func


def get_arguments():
    parser = argparse.ArgumentParser(description='This script enables you to configure IQ Server from JSON\
     data, thus supporting the config-as-code requirement of Sonatype customers')
    parser.add_argument('-a', '--snyk_token', required=True)
    parser.add_argument('-g', '--grp_name', required=True)
    parser.add_argument('-o', '--org_name', required=True)
    parser.add_argument('-c', '--collection_name', required=True)
    parser.add_argument('-v', '--api_ver', default="2024-01-23")

    args = vars(parser.parse_args())
    return args


def remove_collection(headers, args, org, collection_id):
    utils.rest_api.remove_collection(headers, args, org, collection_id)




# Press the green button in the gutter to run the script.
if __name__ == '__main__':

    args = get_arguments()
    os.environ['SNYK_TOKEN'] = args['snyk_token']

    headers = {
      'Content-Type': 'application/vnd.api+json',
      'Authorization': 'token {0}'.format(os.getenv('SNYK_TOKEN'))
    }

    utils.util_func.process_collection(headers, args, remove_collection)


