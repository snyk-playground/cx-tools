import snyk
import requests

current_org = "29157d45-0d1d-48a3-b394-814d5b601e05"
move_org = "a2a20bbf-8363-4517-a13f-ef1f848da02d"
auth_token = "670c96f7-f907-4538-8230-f2435050a5ca"

headers = {
  'Authorization': 'token '+auth_token
}
rest_client = snyk.SnykClient(auth_token, version="2023-06-23", url="https://api.snyk.io/rest")
v1_client = snyk.SnykClient(auth_token)
params = {"limit": 100}
projects = rest_client.get_rest_pages(f"orgs/{current_org}/projects", params=params)

proj_count=0
for curr_proj in projects:
  print(curr_proj['attributes']['name'])
  curr_id=curr_proj['id']
  curr_name=curr_proj['attributes']['name']
  url = "https://snyk.io/api/v1/org/"+current_org+"/project/"+curr_id+"/move"
  payload={
    "targetOrgId": move_org
  }
  print("Moving project "+curr_name+"...")
  requests.request("PUT", url, headers=headers, data=payload)
  proj_count+=1
print("Project move complete. "+str(proj_count)+" projects moved.")

