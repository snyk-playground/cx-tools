# How can customer pull list of all repos imported to Snyk?

## Description:
How can customer pull list of all repos imported to Snyk?

## Instructions
### Option 1 > Python Script : https://gist.github.com/mrzarquon/5abdc2c2c11a5bde685848ff10312955

get a list of all repos in a github integration

All the steps and commands are listed at the bottom of above link.


### Option 2 > using curl and jq in CLI

You can use below Command on your terminal to get the list of repos.

```
curl -s \
   --header "Content-Type: application/json" \
   --header "Authorization: APITOKEN" \
 'https://snyk.io/api/v1/org/OrgId/projects' | jq '.projects'
| jq '.projects[].name'
```
