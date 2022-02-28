# How to Import all Project with suffix

## Description
Customers would like to have a suffix, for versioning for example, into all the projects they are monitoring.

Currently the system supports only changing the project-name if all project flags is not available.

## Proposed Solution
The proposed solution creates a loop on the subfolder and calls snyk monitor, giving the project name as: folder name + suffix

The suffix is got from the first parameter sent, for example:

```
./monitor_add_suffix.bash -v1.0

version=$1

  #monitor root folder
  f=$(pwd)
  filename=`basename ${f%%}`
  #echo $filename"$version"
  snyk monitor --org=67f98cc1-4e0d-4d59-9ca1-8115592bcb2e --project-name=$filename"$version"

  for f in ./*/;
    do
       [ -d $f ]  && cd "$f"
       filename=`basename ${f%%}`
       echo $filename"$version"
       snyk monitor --YOUR-ORG --project-name=$filename"$version"
       cd ..
    done;

```
