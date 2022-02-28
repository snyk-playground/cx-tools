# How to Silence snyk exit code and create advanced conditions to fail the build

## Description:
Customers are requesting to have more control on the exit criteria of the snyk test on the CLI. A common request is the ability to fail a build if found only vulnerabilities with cvss score grater than a specific number (9.5, for example).

This solution allows silencing the the default (product) exit code and creating a new failing condition based on customer decision.

Customers can edit and create new conditions to fail their builds based advanced conditions.

## Pre-Requisites
In order to run this process, you need to have jq installed on your system. Jq installation requires brew installation.

Check if you have brew and jq installed

```
brew -v
jq -help
```
Install brew (if needed):

```
ruby -e "$(curl -fsSL [<https://raw.githubusercontent.com/Homebrew/install/master/install>](<https://raw.githubusercontent.com/Homebrew/install/master/install>))" < /dev/null 2> /dev/null
```
Install jq (if needed):

```
brew install jq
```

## Instructions
Create a bash file, for example cvssDecision.bash

Copy the following code on your cvssDecision.bash file

```
# run chmod 755 cvssDecision.bash  to give run proprieties to the bash file
# run ./cvssDecision.bash 9.5 ; echo "Exit code " $? to see the return code
# Needs jq installed (that needs brew to install)
#comment all echo commands

maxScore=$1
snyk test --json > results.json
## get the exit code on $ variable ##
if [ $? -eq 0 ]
then
  echo "Success: exit code 0."
  rm results.json
  exit 0
else
  ## Reading json  ##
  cvssScores=( $(jq -r '.vulnerabilities[].cvssScore' results.json) )
  echo "Found" ${#cvssScores[@]} "vulns! Let's check cvss scores"

## if found cvss > 9.8 -> exit code 1
    for (( i=0; i<${#cvssScores[@]}; i++ ));
    do
        if (( $(bc <<< "${cvssScores[$i]}>$maxScore") > 0 ));
        then
          echo "Found vuln with cvss score =" "${cvssScores[$i]}" "exiting...";
	          rm results.json
          exit 1
        fi
    done
    echo "all good !"
    rm results.json
    exit 0
fi
```
