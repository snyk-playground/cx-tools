# How to add user to same orgs as other user

## Description
Use this script for add user B to all organizations user A is member.

This scripts will add the user as one role only, regardless the original roles.

Target User must be a group member before assigned to orgs.

The command if [ "$i" -lt 1 ]; then is only for first test → Remove it when ready.

## Script / Code Example
```
set +x
 orgs=($(curl -s \\
     --request GET \\
     --header "Content-Type: application/json" \\
     --header "Authorization: ORIGINAL-USER-TOKEN" \\
'<https://snyk.io/api/v1/orgs>' | jq --raw-output ' .orgs[].slug, .orgs[].id, .orgs[].group.id' ))
total=${#orgs[@]}
let total=total/3
echo "Found" $total "orgs"

for (( i=0; i<$total; i++ ));
do
    let ii=i+total
    let iii=total+total+i
    # Group ID - #org ID - ORG-name
   if [ "$i" -lt 1 ]; then
      echo "----------------"
      echo "${orgs[$iii]}" "\\t" "${orgs[$ii]}" "\\t" "${orgs[$i]}"   ;
      curl --include \\
        --request POST \\
        --header "Content-Type: application/json" \\
        --header "Authorization: YOUR-TOKEN" \\
        --data-binary "{
      \\"userId\\": \\"TARGET-USER_ID\\",
      \\"role\\": \\"collaborator\\"
      }" \\
      '<https://snyk.io/api/v1/group/'"${orgs[$iii]}"'/org/'"${orgs[$ii]}"'/members>'
    fi

done
      echo "----------------"
```
