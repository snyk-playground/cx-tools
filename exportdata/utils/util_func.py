import json

from apis.rest_api import export_group_data, export_status, download_report


def export_issue_details(args):
    group_export = json.loads(export_group_data(args))
    return (group_export["data"]["id"])


def get_export_status(grp_id, export_id):
    return json.loads(export_status(grp_id, export_id))


def download_issue_details_data(args, export_id):
    return download_report(args, export_id)
