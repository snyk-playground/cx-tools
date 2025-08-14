# Bulk Activate / Deactivate Snyk Projects

De / activates projects across multiple Snyk Organisations in a Group.

## Features

`get_projects.py` - gathers project information for entire Snyk Orgnisation. Uses [Snyk's REST API](https://apidocs.snyk.io/).

`change_project_status.py` - De / activates selected projects. Uses [Snyk's V1 API](https://snyk.docs.apiary.io/).

## Configuration

Install dependencies
```sh
pip install -r requirements.txt
```

Update variables in `get_projects.py`. Get the latest API Version from [Snyk's REST API](https://apidocs.snyk.io/)
```py
API_VERSION = "2024-08-15"
RATE_LIMIT_DELAY = 0.2 (in seconds)
```

## Usage

### Gather project information 

Run the script locally

```sh
python3 get_projects.py --group YOUR_GROUP_ID --token your_api_token
```

Script will output `project_data.json` file. Edit the file as necessary. Example below

```json
[
    {
        "org_name": "Test_Org",
        "org_id": "**************",
        "project_name": "nodejs-goof/nodejs-goof(main)",
        "project_id": "**************",
        "type": "sast",
        "target_file": "",
        "status": "active"
    }
]
```

### Activate / Deactivate Projects

```sh
python3 change_proj_status.py project_data.json --action activate/deactivate --token your_api_token
```


## Filter Results using jq

https://jqlang.github.io/jq/manual/

### Project Status

`|  jq '.[] | select(.status == "[active|inactive]")'`

### Snyk Organisation Name

`|  jq '.[] | select(.org_name == "[SnykOrgName]")'`

### Target File Name

`| jq '.[] | select(.target_file | contains("yaml"))`

### Snyk Product Type

`|  jq '.[] | select(.project_type == "sast")'`


#### All project types available at:
https://docs.snyk.io/snyk-api/api-endpoints-index-and-tips/project-type-responses-from-the-api

