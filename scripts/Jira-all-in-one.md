# all-in-one.py
This script will take all critical issues within a project and create a single Jira ticket

## Script for all-in-one.py:
```
#This script will take all critical issues within a project and create a single Jira ticket
import requests
import json

#Snyk Parameters
org_id="xxxxxx"
project_id="xxxxxxx"
snyk_token="xxxxxxx"
snyk_headers = {
  'Authorization': 'token '+snyk_token,
  'Content-Type': 'application/json'
}

#Jira Parameters
jira_token="xxxx"
jira_proj_id="xxx"

#Pull in project info from Snyk
snyk_url="https://snyk.io/api/v1/org/"+org_id+"/project/"+project_id
snyk_body={}

response = requests.request("GET", snyk_url, headers=snyk_headers, data=snyk_body)
response_dict = response.json()
crit_count=str((response_dict['issueCountsBySeverity']['critical']))
proj_name=response_dict['name']
proj_link=response_dict['browseUrl']

#Pull in list of critical issues from the project
snyk_url="https://snyk.io/api/v1/org/"+org_id+"/project/"+project_id+"/aggregated-issues"

snyk_body= json.dumps({
  "includeDescription": False,
  "includeIntroducedThrough": False,
  "filters": {
    "severities": [
      "critical"
    ],
    "exploitMaturity": [
      "mature",
      "proof-of-concept",
      "no-known-exploit",
      "no-data"
    ],
    "types": [
      "vuln",
      "license"
    ],
    "ignored": False,
    "patched": False,
    "priority": {
      "score": {
        "min": 0,
        "max": 1000
      }
    }
  }
})

response = requests.request("POST", snyk_url, headers=snyk_headers, data=snyk_body)
response_dict = response.json()

#Creating the payload for the Jira ticket
payload=  {
    "fields": {
       "project":
       {
          "key": jira_proj_id
       },
       "summary": proj_name+" - "+crit_count+" Critical Vulnerabilities",
		 "description": {
            "version": 1,
            "type": "doc",
            "content": [
                {
                    "type": "paragraph",
                    "content": [
                        {
                            "type": "text",
                            "text": "There are currently "+crit_count+" Critical Vulnerabilities in your project. Click "
                        },                        
						{
                            "type": "text",
                            "text": "here",
                            "marks": [
                                {
                                    "type": "link",
                                    "attrs": {
                                        "href": proj_link
                                    }
                                }
                            ]
                        },
                        {
                            "type": "text",
                            "text": " to access the project."
                        }
                    ]
                }
            ]
        },
       "issuetype": {
          "name": "Task"
       }
   }
}

desc_count=1
while response_dict['issues']:
	issue = response_dict['issues'].pop()

	payload['fields']['description']['content'].append({
                    "type": "paragraph",
                    "content": [
                        {
                            "type": "text",
                            "text": issue['pkgName']+" - "+issue['issueData']['title'],
                            "marks":[
                            {
                            	"type": "strong"
                            }
                            ]
                        },   
                       	{
                            "type": "text",
                            "text": "\nCVSS Score: "+str(issue['issueData']['cvssScore'])+"\nMaturity: "+issue['priority']['factors'][0]['description']
                        },                      
								{
                            "type": "text",
                            "text": "\nMore info",
                            "marks": [
                                {
                                    "type": "link",
                                    "attrs": {
                                        "href": issue['issueData']['url']
                                    }
                                }
                            ]
                        }
                    ]
                }
                )	

	desc_count+=1
url = "https://snyksec.atlassian.net/rest/api/3/issue"
payload=json.dumps(payload)

headers = {
  'Authorization': 'Basic xxxxxxxxx',
  'Content-Type': 'application/json',
  'Cookie': 'xxxxx'
}

response = requests.request("POST", url, headers=headers, data=payload)
print(response.text)
```
