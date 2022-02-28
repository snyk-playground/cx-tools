# How to delete all projects of a repo

## Description:
Works only for CLI. For SCM need to change for browserUrl instead of repoUrl


## Instructions
call : ./your-script-file <API-Token> <RepoName> <org-id>


```
set +x
APItoken=$1
repoUrl=$2
org=$3

 projs=($(curl -s \
     --request GET \
     --header "Content-Type: application/json" \
     --header "Authorization: ${APItoken}" \
"https://snyk.io/api/v1/org/${org}/projects" | jq --raw-output ' .projects[].id, .projects[].remoteRepoUrl, .projects[].name' ))
total=${#projs[@]}
let total=total/3


for (( i=0; i<$total; i++ ));
do
    let ii=i+total
    let iii=total+total+i
    #echo "----------------"
    #echo "${projs[$iii]}" "\t" "${projs[$ii]}" "\t" "${projs[$i]}"   ;
    # Group ID - #org ID - ORG-name
   if  [ "${projs[$ii]}" = "$repoUrl" ] ; then
      #echo "----------------"
      #echo "Project\tName: ${projs[$iii]}" "\tRepo: " "${projs[$ii]}" "\tID :" "${projs[$i]}"   ;

      curl --include \
           --request DELETE \
           --header "Content-Type: application/json" \
           --header "Authorization: ${APItoken}" \
        "https://snyk.io/api/v1/org/${org}/project/${projs[$i]}"
    fi

done
      echo "------ Deleted projects from ${repoUrl} on org ${org}---------------"
```
