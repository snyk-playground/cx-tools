![snyk-oss-category](https://github.com/snyk-labs/oss-images/blob/main/oss-example.jpg)

<br/>
<div align="center">
This is a list of examples and scripts compiled by the Snyk Customer Experience teams for the purpose of solving specific use cases raised by customers.
</div>
<br/>


# Parse Integrations
This utility allows Snyk customers to persist the configuration settings for their integrations to a file. Persisted
data may be for a single group (all orgs) or a comma delimited list of orgs within that group. When persisted, the 
org name and integration name are augmented by their internal Snyk id(s). These id(s) are parsed by the update script.

## How to call parse_integrations.py
````
python3 parse_integrations.py
    --snyk_token="<snyk-token-value>" 
    --grp_name="<snyk-group-name>"
    --org_names="<target-snyk-org-name1,target-snyk-org-name2>" 
    --api_ver="<snyk-rest-api-version>"

python3 parse_integrations.py
    --snyk_token="<snyk-token-value>" 
    --grp_name="kevin.matthews Group"
    --org_names="Org1,Org2" 
    --api_ver="2024-08-15"

Note that the org_names argument is optional.
````

# Update Integrations

After bulk editing the configuration pertaining to their integrations offline, this utility allows Snyk customers 
to upload that configuration at scale across their Snyk deployment. The persisted json file can be edited to ensure 
configuration that is aligned to the customer's DevSecOps maturity and ambitions. Speak with the TSM team for 
guidance as to what configuration settings align with your requirements at this time.

## How to call update_integrations.py
````
python3 update_integrations.py
    --snyk_token="<snyk-token-value>" 
    --config_file="<json-config-filename>"
    --api_ver="<snyk-rest-api-version>"

python3 parse_integrations.py
    --snyk_token="<snyk-token-value>" 
    --config_file="kevin.matthews Group--Org1Org2.json"
    --api_ver="2024-08-15"

````

### Note:
At the time of writing, I am required to use a mix of GA and beta REST APIs. As the beta APIs become GA, so I will 
update this software.