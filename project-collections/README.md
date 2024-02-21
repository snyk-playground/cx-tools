# Collections
## Build Collections
A that creates a collection and/or adds tagged projects to it.

## Use Case
Collections allow snyk projects within a given organisation to be viewed through a single pane of glass. Projects may
be tagged in order to provide a key that identifies them as a collective. These tagged projects are added to the 
collection.

## Call predicate
build_collection -a \<snyk-auth-token\> -v "snyk-rest-api-version" -g "snyk-group-name" -o "snyk-org-name" -c "squad-3" -t "tag-name:tag-value" -s "critical,high"

## Example usage:
#### Full argument names
build_collection --snyk_token \<snyk-auth-token\> 
    --grp_name "kevin.matthews Group" --org_name "PR Test Org" --collection_name="squad-3" --project_tags "squad-name:squad-3" --effective_severity_level="critical,high"  --api_ver "2024-01-23"
##### Assuming default arg values where possible
tagged_project_issues --snyk_token \<snyk-auth-token\> 
    --grp_name "kevin.matthews Group" --org_name "PR Test Org" --collection_name="squad-3" --project_tags "squad-name:squad-3"

#### Argument flags
tagged_project_issues -a \<snyk-auth-token\> -g "kevin.matthews Group" -o "PR Test Org" -c "squad-3" -t "squad-name:squad-3" -s "critical,high" -v "2024-01-23"
##### Assuming default arg values where possible
tagged_project_issues -a \<snyk-auth-token\> -g "kevin.matthews Group" -o "PR Test Org" -c "squad-3" -t "squad-name:squad-3"

### Arguments
- --snyk_token <snyk_auth_token>
- --grp_name "Snyk group name in which tagged projects are to be parsed"
- --org_name "Snyk org name in which tagged projects are to be parsed"
- --collection_name "The name of the collection to be created and to which tagged projects will be added."
- --project_tags "Comma delimited list of 'tags', all of which must be assigned to a project for it to be identified"
- --effective_severity_level "Comma separated list of severities to be identified in tagged project issues payload"
- --api_ver "The version of the Snyk API to be used (default recommended)"

