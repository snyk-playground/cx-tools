# User Management
## List Users
A script to list all users within all or selected named orgs that assume specified roles. 
This script pertains to a single named group.

## Use Case
A customer has requested a list of 'admins' within their principal group. This script allows the flexibility 
to specify named orgs or default to all. Roles must be specified and comma delimited.

## Call predicate
list_users -a \<snyk-auth-token\> -g "Group" -r "admin,collaborator" -o <org_name_1>,<org_name_2> -v "2024-05-23"

## Example usage:
#### Full argument names
list_users --snyk_token \<snyk-auth-token\> --grp_name "kevin.matthews Group" --org_name Test_1,Test_2 --roles "admin,collaborator" -v "2024-05-23"

##### Assuming default arg values where possible
list_users --snyk_token \<snyk-auth-token\> --grp_name "kevin.matthews Group" --roles "admin,collaborator"


#### Argument flags
remove_collection -a \<snyk-auth-token\> -g "kevin.matthews Group" -o "PR Test Org" -c "squad-3" -v "2024-01-23"
##### Assuming default arg values where possible
remove_collection -a \<snyk-auth-token\> -g "kevin.matthews Group" -o "PR Test Org" -c "squad-3"

### Arguments
- --snyk_token <snyk_auth_token>
- --grp_name "Snyk group name in which tagged projects are to be parsed"
- --org_names "Snyk org name(s) in which tagged projects are to be parsed. Comma delimited."
- --roles "Snyk role(s) to be retrieved. Comma delimited."
- --api_ver "The version of the Snyk API to be used (default recommended)"

### Note 
Some of the APIs used are in beta. Others are GA. As the beta's become GA, I will remove the 'hard-coded' use of their 
beta counterparts. Meantime, please DO NOT specify a beta version of an API should you wish to choose a specific 
version. It is recommended at this time that you allow the default version to be used.
