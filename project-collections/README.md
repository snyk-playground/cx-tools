# Collections
## Build Collection
A script that creates a collection of projects within a named organisation, where those projects have a specified 
Snyk tag. The collection is created if it does not exist. The script synchronises the collection with the specified 
tag. Projects to which the specified tag has been added or removed will be reflected when the collection is refreshed.

This script can be run periodically from pipelines in order to ensure the collection remains up to date.

## Use Case
Collections allow snyk projects within a given organisation to be viewed through a single pane of glass. Projects may
be tagged in order to provide a key that identifies them as a collective. These tagged projects are added to the 
collection. An example tag might be 'classification:secret'

## Call predicate
build_collection -a \<snyk-auth-token\> -v "snyk-rest-api-version" -g "snyk-group-name" -o "snyk-org-name" -c "collection-name" -t "tag-name:tag-value"

## Example usage:
#### Full argument names
build_collection --snyk_token \<snyk-auth-token\> 
    --grp_name "kevin.matthews Group" --org_name "PR Test Org" --collection_name="secret" --project_tags "classification:secret" --api_ver "2024-01-23"
##### Assuming default arg values where possible
build_collection --snyk_token \<snyk-auth-token\> 
    --grp_name "kevin.matthews Group" --org_name "PR Test Org" --collection_name="secret" --project_tags "classification:secret"


## Remove Collection
A script that deletes a named collection. This is the brut force full delete of the collection. This script does not 
delete a sub-set of the projects within the collection.

## Use Case
A collection abstracts a view of assigned projects. You need to delete the collection.

## Call predicate
remove_collection -a \<snyk-auth-token\> -v "snyk-rest-api-version" -g "snyk-group-name" -o "snyk-org-name" -c "secret"

## Example usage:
#### Full argument names
remove_collection --snyk_token \<snyk-auth-token\> 
    --grp_name "kevin.matthews Group" --org_name "PR Test Org" --collection_name="secret" --api_ver "2024-01-23"
##### Assuming default arg values where possible
remove_collection --snyk_token \<snyk-auth-token\> 
    --grp_name "kevin.matthews Group" --org_name "PR Test Org" --collection_name="secret" 



#### Argument flags
remove_collection -a \<snyk-auth-token\> -g "kevin.matthews Group" -o "PR Test Org" -c "secret" -v "2024-01-23"
##### Assuming default arg values where possible
remove_collection -a \<snyk-auth-token\> -g "kevin.matthews Group" -o "PR Test Org" -c "secret"

### Arguments
- --snyk_token <snyk_auth_token> (Optional. SNYK_TOKEN read from environment if not specified)
- --grp_name "Snyk group name in which tagged projects are to be parsed"
- --org_name "Snyk org name in which tagged projects are to be parsed"
- --collection_name "The name of the collection to be created and to which tagged projects will be added."
- --project_tags "Comma delimited list of 'tags', all of which must be assigned to a project for it to be identified"
- --api_ver "The version of the Snyk API to be used (default recommended)"

````
Note that the snyk_token and api_ver arguments are optional.

Some of the APIs used are in beta. Others are GA. As the beta's become GA, I will remove the 'hard-coded' use of their 
beta counterparts. Meantime, please DO NOT specify a beta version of an API should you wish to choose a specific 
version. It is recommended at this time that you allow the default version to be used.
