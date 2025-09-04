import argparse
import os
import sys
import time

from exportdata.utils.util_func import export_issue_details, get_export_status, download_issue_details_data
from datetime import datetime, timedelta
from apis.rest_api import get_orgs_in_group


def get_n_days_ago(n):
    try:
        # If the value was passed as an integer offset of the number of days relative to today
        now = datetime.utcnow()
        n_days_ago = now + timedelta(days=int(n))
        return n_days_ago.strftime("%Y-%m-%dT00:00:00Z")
    except ValueError:
        # If it was passed as a formatted string
        return n

def read_columns_file(dataset):
    # Read the file and strip whitespace
    filename = "issues-columns.txt"
    if dataset == "usage":
        filename = "usage-columns.txt"

    with open(filename, "r") as file:
        columns = [line.strip() for line in file if line.strip()]
    return columns


def split_and_clean(input_string):
    return [item.strip() for item in input_string.split(',') if item.strip()]


def get_arguments():
    parser = argparse.ArgumentParser(description='This script enables you to export issues pertinent to an identified '
                                                 'Snyk group id. It supportes the api arguments and thus allows '
                                                 'flexibility to specify the payload required.')
    parser.add_argument('-a', '--snyk_token', default=None)
    parser.add_argument('-g', '--grp_id', required=True)
    parser.add_argument('-d', '--dataset', required=True)
    parser.add_argument('-f', '--introduced_from', default=None)
    parser.add_argument('-t', '--introduced_to', default=None)
    parser.add_argument('-u', '--updated_from', default=None)
    parser.add_argument('-z', '--updated_to', default=None)
    parser.add_argument('-o', '--orgs', default=None)
    parser.add_argument('-e', '--env', default=None)
    parser.add_argument('-l', '--lifecycle', default=None)
    parser.add_argument('-c', '--columns', default=None)
    parser.add_argument('-v', '--api_ver', default="2024-10-15")
    parser.add_argument('-s', '--output_file', default="snyk_export.csv")

    args = vars(parser.parse_args())
    if args["snyk_token"]:
        os.environ["SNYK_TOKEN"] = args["snyk_token"]

    os.environ["API_VERSION"] = args["api_ver"]
    return args


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    args = get_arguments()
    grp_id = args['grp_id']

    # Format the introduced start date
    if args["introduced_from"]:
        args["introduced_from"] = get_n_days_ago(args["introduced_from"])

    # Format the introduced end date
    if args["introduced_to"]:
        args["introduced_to"] = get_n_days_ago(args["introduced_to"])

    # Format the updated start date
    if args["updated_from"]:
        args["updated_from"] = get_n_days_ago(args["updated_from"])

    # Format the updated end date
    if args["updated_to"]:
        args["updated_to"] = get_n_days_ago(args["updated_to"])

    # Parse the columns
    if not args["columns"]:
        args["columns"] = read_columns_file(args["dataset"].lower())
    else:
        args["columns"] = split_and_clean(args["columns"])

    # local group identifier
    grp_id = args["grp_id"]

    # Parse the orgs
    if not args["orgs"]:
        args["orgs"] = get_orgs_in_group(grp_id)
    else:
        args["orgs"] = split_and_clean(args["orgs"])

    export_id = export_issue_details(args)
    response = get_export_status(grp_id, export_id)
    while response["data"]["attributes"]["status"] in ("STARTED", "PENDING"):
        time.sleep(1)
        print(".", end='', flush=True)
        response = get_export_status(grp_id, export_id)
    if response["data"]["attributes"]["status"] == "FINISHED":
        sys.exit(download_issue_details_data(args, export_id))
    else:
        print(f"Something went wrong! {response}")


