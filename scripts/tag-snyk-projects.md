# Tag projects in Snyk

## Description

Use this script to tag your Snyk projects while being imported, in this example we will use Github as the source of the projects and tag them with an appId value

## Flow and Endpoints

### Flow:

- List of projects from Snyk
    1. List all project API using
        1. Origin: github
        2. Name: <value>
2. For each project
    1. ⚠️ 1 Github Repo -> Multiple projects into Snyk → 1 GH repo / 1 tag
    2. Fetch tag

Apply appId tag to project `appId: <VALUE>`

### APIs used:

**Fetching project (with or without tags associated with them)**

[https://snyk.docs.apiary.io/#reference/projects/all-projects/list-all-projects](https://snyk.docs.apiary.io/#reference/projects/all-projects/list-all-projects)

**Adding a tag**

[https://snyk.docs.apiary.io/#reference/projects/project-tags/add-a-tag-to-a-project](https://snyk.docs.apiary.io/#reference/projects/project-tags/add-a-tag-to-a-project)

## Code examples

(Bash)

```bash
#!/usr/bin/env bash

set -eux

IMPORT=$1
PROJECT=$2
LABEL=$3
SNYK_ORG=$4

SUFFIX=${SUFFIX:-}

curl -s -H "Authorization: token $TOKEN" -H 'Content-Type: application/json' $IMPORT |\
	jq -r '.logs|.[]|select(.name=="'$SNYK_ORG'/'$PROJECT'").projects|.[].projectUrl'

projects=$(curl -s -H "Authorization: token $TOKEN" -H 'Content-Type: application/json' $IMPORT \
	jq -r '.logs|.[]|select(.name=="'$SNYK_ORG'/'$PROJECT'").projects|.[].projectUrl' |\
	awk '/-/' | gsed 's_.*/project/__;s_"__')
for p in $projects; do
	echo $p
	curl -s -X POST -H "Authorization: token $TOKEN" -H 'Content-Type: application/json' --data-binary '{"key":"label","value":"'$LABEL'"}' https://snyk.io/api/v1/org/$ORG/project/$p/tags${SUFFIX}
done
```