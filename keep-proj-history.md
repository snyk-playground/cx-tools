# How to Keep Projects History snapshots

## Description:
Customers are requesting the ability of keeping a history of their versions snapshots, so they will have the ability to better track their progress.

The request is to have a tree like : Snyk Org (Customer Team) -> Snyk repo (Team Application) -> Snyk project (Version of an Application)

The current functionality overrides the snapshot of the version every time a snyk monitor runs.

## Limitations:
As the solution is based on --project-name= option, it cannot be used for --all-projects, therefore is needed the run projects one by one.

## Instructions
Create a file called : versionConfig.txt

File format:
```
version your_version_number
project your_project_name
repo the_repo_name
```
File example:
```
version v1.3
project io.github.snyk:todolist-mvc
repo goof
```
Create a bash file : snykMonitorbyVersion.bash

```
# run chmod 755 snykMonitorbyVersion.bash  to give run proprieties to the bash file
# run ./cvssDecision.bash 9.5 ; echo "Exit code " $? to see the return code
# Needs jq installed (that needs brew to install)
#comment all echo commands
orgName=$1

file="./versionConfig.txt"

while read var value
do
    export "$var"="$value"
done < $file

echo "var:" "$project" "$org"

#set -o xtrace
#set +o xtrace to revert

snyk monitor --remote-repo-url=${repo}-${version} --org="${orgName}"  --project-name=${project}-${version}
```
Give run proprieties to the bash file

```
 chmod 755 snykMonitorbyVersion.bash
```

Run the script passing (or not) your org name:

```
./snykMonitorbyVersion.bash org-one
```

Your projects will be stored in different snapshots


### Improvements
Customers can set the parameters on environment variables and get directly from there, and in case running CI tool, these can be taken from variables values on the CI/CD tool, calling the snyk monitor / test directly with the right arguments.

Changing only the --project-name and keep it with the version will result on having all versions displayed under the same repo url as shown on the following example:




## Alternative Solution
Bamboo
Example on how should be with bamboo variables (sure about the right bamboo syntax):

snyk test --project-name=${bamboo.deploy.project}-${bamboo.deploy.version}


Note: Changing only the --remote-repo-url will not work, since it will override the repo name every new run.
