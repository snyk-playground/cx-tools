# Tagged Project Issues
A utility that pulls all vulnerabilities for projects annotated with a snyk tag(s).

## Use Case
<p>This utility allows Snyk customers to retrieve vulnerability data for tagged projects that co-exist within a single 
organisation. A customer who has multiple development teams whose repositories are abstracted within a single Snyk organisation, 
can use this utility to view vulnerabilities pertinent to a single development team only. 

## Call predicate
tagged_project_issues -a \<snyk-auth-token\> -v "snyk-rest-api-version" -g "snyk-group-name" -o "snyk-org-name" -t "tag-name:tag-value" -s "critical,high"

## Example usage:
#### Full argument names
tagged_project_issues --snyk_token \<snyk-auth-token\> 
    --grp_name "kevin.matthews Group" --org_name "PR Test Org" --project_tags "squad-name:squad-3" --effective_severity_level="critical,high"  --api_ver "2024-01-23"
##### Assuming default arg values where possible
tagged_project_issues --snyk_token \<snyk-auth-token\> 
    --grp_name "kevin.matthews Group" --org_name "PR Test Org" --project_tags "squad-name:squad-3"

#### Argument flags
tagged_project_issues -a \<snyk-auth-token\> -g "kevin.matthews Group" -o "PR Test Org" -t "squad-name:squad-3" -s "critical,high" -v "2024-01-23"
##### Assuming default arg values where possible
tagged_project_issues -a \<snyk-auth-token\> -g "kevin.matthews Group" -o "PR Test Org" -t "squad-name:squad-3"

### Arguments
- --snyk_token <snyk_auth_token>
- --grp_name "Snyk group name in which tagged projects are to be parsed"
- --org_name "Snyk org name in which tagged projects are to be parsed"
- --project_tags "Comma delimited list of 'tags', all of which must be assigned to a project for it to be identified"
- --effective_severity_level "Comma separated list of severities to be identified in tagged project issues payload"
- --api_ver "The version of the Snyk API to be used (default recommended)"


### Note: 
<p>Search may comprise multiple tags (comma delimited) and multiple severity thresholds (comma delimited). These are 
logically AND'd and must all be annotated to a project in order for results to be returned. If a project is annotated 
with multiple tags, use of one of those tags by this utility will return results.</p>
