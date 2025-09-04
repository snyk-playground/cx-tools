![snyk-oss-category](https://github.com/snyk-labs/oss-images/blob/main/oss-example.jpg)

<br/>
<div align="center">
This is a list of examples and scripts compiled by the Snyk Customer Experience teams for the purpose of solving specific use cases raised by customers.
</div>
<br/>

### Environment:
Ensure that the 'cx-tools' directory is included in your PYTHONPATH environment variable. This ensures that the import 
statements for modules in sub folders are resolved. 

This software has been written and tested using python 3.10.4

````
    cd cx-tools
    export PYTHONPATH=`pwd`
````

# Export Group Data
This utility calls the ['export'](https://apidocs.snyk.io/?version=2024-10-15#post-/groups/-group_id-/export) api in order to allow issues to be exported to a csv file. This matches the behaviour
of the UI when viewing the Issue Details report. You should use this mechanism if you wish to download large volumes
of data that would otherwise take a significant number of api cals using the ['issues'](https://apidocs.snyk.io/?version=2024-10-15#get-/groups/-group_id-/issues) api.
The export api now incorporates support to download usage data. The 'dataset' argument allows users to choose issues or usage data download.

## How to call export-data.py
````
Run from the cx-tools/exportdata directory.

python3 export-data.py
    --snyk_token="<snyk-token-value>" 
    --grp_id="<snyk-group-id>"
    --dataset="issues|usage"
    --introduced_from="Note A"
    --introduced_to="Note A"
    --updateed_to="Note A"
    --updated_from="Note A"
    --orgs="<target-snyk-org-id1,target-snyk-org-id2>" 
    --env="<environment>"
    --lifecycle="<lifecycle>"
    --columns="Note B"
    --api_ver="2024-10-15"
    --output_file="<output_file.csv>"


python3 export-data.py
    --snyk_token="<snyk-token-value>" 
    --dataset="issues"
    --grp_id="123-4567-890"
    --introduced_from="-30"
    --introduced_to="+1"
    --updated_to=""
    --updated_from=""
    --orgs="123-4567-890, 890-7654-321" 
    --env=""
    --lifecycle=""
    --columns="SCORE, CVE"
    --api_ver="2024-10-15"
    --output_file="snyk_export.csv"


````
Note that the only mandatory arguments are the 'grp_id' and 'dataset'. All other arguments have default values.

Note A: Dates - You may specify a relative offset value (ie -30 or +1) with respect to today's date. Alternatively, 
you may specify the date-time format to which the offset is converted ("2025-07-21T00:00:00Z") for absolute dates.

Note B: Columns - You may specify comma seperated column name (ie "SCORE, CVE"). Alternatively, leave this blank and the
['issues-columns.txt'](./issues-columns.txt) or ['usage-columns.txt'](./usage-columns.txt) file will be parsed. 
You can of course edit this. Ensure you refer to Snyk's ['Export API:Available Columns'](https://docs.snyk.io/snyk-api/using-specific-snyk-apis/export-api-specifications-columns-and-filters#available-columns)

````
