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

# Parse Integrations
This utility allows Snyk customers to persist the configuration settings for their integrations to a file. Persisted
data may be for a single group (all orgs) or a comma delimited list of orgs within that group. When persisted, the 
org name and integration name are augmented by their internal Snyk id(s). These id(s) are parsed by the update script.

## How to call parse_integrations.py
````
Run from the cx-tools directory.

python3 integrations/parse_integrations.py
    --snyk_token="<snyk-token-value>" 
    --grp_name="<snyk-group-name>"
    --org_names="<target-snyk-org-name1,target-snyk-org-name2>" 
    --api_ver="<snyk-rest-api-version>"

python3 integrations/parse_integrations.py
    --snyk_token="<snyk-token-value>" 
    --grp_name="kevin.matthews Group"
    --org_names="Org1,Org2" 
    --api_ver="2024-08-15"

Note that the org_names argument is optional.
````

# Update Integrations

After bulk editing the configuration pertaining to their integrations offline, this utility allows Snyk customers 
to upload that configuration at scale across their Snyk deployment. The persisted json file can be edited to ensure 
configuration that is aligned to the customer's DevSecOps maturity and ambitions. Alternatively, template configuration 
can be passed to this script, with the integration config settings applied from the template configuration file.

Speak with the TSM team for guidance as to what configuration settings align with your requirements at this time.

## How to call update_integrations.py
### Apply configuration from a persisted configuration file
````
Run from the cx-tools directory.

python3 integrations/update_integrations.py
    --snyk_token="<snyk-token-value>" 
    --config_file="<json-config-filename>"
    --api_ver="<snyk-rest-api-version>"

python3 integrations/update_integrations.py
    --snyk_token="<snyk-token-value>" 
    --config_file="integrations/kevin.matthews Group--Org1Org2.json"
    --api_ver="2024-08-15"
````
### Apply configuration from a template configuration file
````
Run from the cx-tools directory.

python3 integrations/update_integrations.py
    --snyk_token="<snyk-token-value>" 
    --config_file="<json-config-filename>"
    --template="<json-template-config>"
    --api_ver="<snyk-rest-api-version>"

python3 integrations/update_integrations.py
    --snyk_token="<snyk-token-value>" 
    --config_file="integrations/kevin.matthews Group--Org1Org2.json"
    --template="integrations/templates/preventnewissues.json"
    --api_ver="2024-08-15"

````

# Benchmark Adoption Maturity
This utility allows Snyk customers to parse the persisted configuration and benchmark its alignment with a template
configuration file. Disparities between the persisted configuration and the template configuration are identified. The 
'mid-journey' adoption phases have a template that baselines all settings (be they active or not) and also a minimum 
requirements template that comprises only those config attributes that must be active to achieve the adoption maturity 
phase. 

## How to call benchmark_adoption_maturity.py
````
Run from the cx-tools directory.

python3 integrations/benchmark_adoption_maturity.py
    --snyk_token="<snyk-token-value>" 
    --config="<json-config-filename>"
    --template="<json-template-config>"
    --api_ver="<snyk-rest-api-version>"

python3 integrations/parse_integrations.py
    --snyk_token="<snyk-token-value>" 
    --config "integrations/kevin.matthews Group_Snyk_Integrations.json"
    --template "integrations/templates/preventnewissues.json"
    --api_ver="2024-08-15"

````

### Note:
At the time of writing, I am required to use a mix of GA and beta REST APIs. As the beta APIs become GA, so I will 
update this software.

I'm still trying to nail this down, but I think I have observed some gremlins in terms of data the integrations api 
that the UI does not. To that end the following config attributes must be set using the api only:

- autoPrivateDepUpgradeEnabled
- pullRequestAssignment
  - type

If you know definitively where/if the gremlins exist, please speak up! That said, i've tested this software well enough 
to be certain that it works! Fix any api nuances and the mechanics of how this works will seamlessly consume the change.