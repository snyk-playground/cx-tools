# How to Get Last Project Monitor

## Description:
Provide report for last monitor time for each one of the projects on a given organisation.

## Script Example
```
projects=($(curl -s \\
     --request POST \\
     --header "Content-Type: application/json" \\
     --header "Authorization: YOUR-TOKEN" \\
     --data-binary "{
  \\"filters\\": {
    \\"userId\\": \\"\\",
    \\"email\\": \\"\\",
    \\"event\\": \\"org.project.monitor\\",
    \\"projectId\\": \\"\\"
  }
}" \\
'<https://snyk.io/api/v1/org/YOUR-ORG/audit>' | jq '. | group_by(.projectId) | map(unique | max_by(.created)) | .[].projectId, .[].created, .[].content.projectName' ))
total=${#projects[@]}
let total=total/3
echo "Found" $total "projects"

echo "Project Id\\tProject Name\\tMonitored on"

for (( i=0; i<$total; i++ ));
do
    let ii=i+total
    let iii=ii+total    
    #echo "Project =" "${projects[$i]}" "- " "${projects[$iii]}"  "- monitored on " ${projects[$ii]};
    echo "${projects[$i]}" "\\t" "${projects[$iii]}"  "\\t" ${projects[$ii]};
done
```
