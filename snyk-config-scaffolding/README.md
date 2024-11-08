
![snyk-oss-category](https://github.com/snyk-labs/oss-images/blob/main/oss-example.jpg)

<br/>
<div align="center">
This is a list of examples and scripts compiled by the Snyk Customer Experience teams for the purpose of solving specific use cases raised by customers.
</div>
<br/>


# Snyk-Scaffold
The utility can be called within CICD pipelines. It enables Snyk customers to scaffold the following configuration 
within the Snyk platform:

- target organisation
- service account with a named group role scope within the created target organisation

These artefacts will only be created if they do not exist. Upon creation of the service account, an auth key for that
account will be returned by way of exit code. This auth key cannot be returned thereafter and so users are reminded to 
store it securely within their environment for subsequent use by their pipeline. Creation of the target organisation and 
associated service account should abstract all repository scans for a given application within your estate. This ensures 
an (Application 1:1 Snyk Organisation) mapping in accordance with recommended best practice.

Customers are advised to build a facade service in front of snyk-scaffold, where the facade will be called directly from 
CICD pipelines. This ensures the Snyk group auth key that is required in order to scaffold Snyk configuration for the 
pipeline will be kept within a restricted environmental context. 

The script returns the service account token for the **newly** created organisation. This value may be propagated to 
the environment as follows:

```
    export SNYK_TOKEN=token-value
```


## How to call Snyk-Scaffold
````
python3 Snyk-Config-Scaffolding/src/snyk-scaffold.py
    --group_name="<snyk-group-name>"
    --group_svc_ac_token="<snyk-group-service-account-token-value>" 
    --group_role_name="<name>"
    --org_name="<target-snyk-org-name>" 
    --org_service_account_name="<name>" 
    --api_ver="<snyk-rest-api-version>"
    --template_org_id="<existing-org-id-to-be-copied-when-creating-new-org>"

python3 Snyk-Config-Scaffolding/src/snyk-scaffold.py
    --group_name="kevin.matthews Group"
    --group_svc_ac_token="<snyk-group-service-account-token-value>"
    --group_role_name="CICD"
    --org_name="Kevin-Test2"
    --org_service_account_name="CICD"
    --api_ver="2024-08-15"
    --template_org_id="<your-template-org-id>"


Note that the template_org_id is optional.
````

# Snyk-Org-Id
The utility can be called within CICD pipelines. It enables Snyk customers to retrieve the organisation id for a named 
organisation. It parses the SNYK_TOKEN value from within the environment in order to authenticate when calling Snyk
APIs.


## How to call Snyk-Org-Id
````
python3 Snyk-Config-Scaffolding/src/snyk-org-id.py
    --group_name="<snyk-group-name>"
    --org_name="<target-snyk-org-name>" 
    --api_ver="<snyk-rest-api-version>"
    --return="SLUG|ID"

python3 Snyk-Config-Scaffolding/src/snyk-org-id.py
    --group_name="kevin.matthews Group"
    --org_name="Kevin-Test2"
    --api_ver="2024-08-15"
    --return="SLUG"
````

### Note:
At the time of writing, I am required to use a mix of GA and beta REST APIs. As the beta APIs become GA, so I will 
update this software.