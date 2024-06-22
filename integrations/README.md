![snyk-oss-category](https://github.com/snyk-labs/oss-images/blob/main/oss-example.jpg)

# Integrations
## Parse Integrations
A script to list all integration settings within all or selected named orgs. 
This script pertains to a single named group.

## Use Case
As a TSM I want to understand the maturity of my customer in terms of Snyk adoption. Parsing the integration settings
enables me to assess adoption maturity and identify recommendation to achieve increased maturity.

## Call predicate
Integrations -a \<snyk-auth-token\> -g "Group" -o <org_name_1>,<org_name_2> -v "2024-05-23"

## Example usage:
#### Full argument names
Integrations --snyk_token \<snyk-auth-token\> --grp_name "kevin.matthews Group" --org_name Test_1,Test_2 -v "2024-05-23"

##### Assuming default arg values where possible
Integrations --snyk_token \<snyk-auth-token\> --grp_name "kevin.matthews Group"


### Arguments
- --snyk_token <snyk_auth_token>
- --grp_name "Snyk group name in which tagged projects are to be parsed"
- --org_names "Snyk org name(s) in which tagged projects are to be parsed. Comma delimited."
- --api_ver "The version of the Snyk API to be used (default recommended)"

### Note 
Some of the APIs used are in beta. Others are GA. As the beta's become GA, it will become necessary to remove the 'hard-coded' use of their 
beta counterparts. Meantime, please DO NOT specify a beta version of an API should you wish to choose a specific 
version. It is recommended at this time that you allow the default version to be used.
