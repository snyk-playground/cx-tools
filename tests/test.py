import snyk
import os 

repoUrlToDelete = "https://github.com/olegs-dev-team-1/node-goof-new/tree/olegstest"
client = snyk.SnykClient("c5e5713f-5167-4ff6-b6af-a44c4f831b1a")
org = client.organizations.get("29157d45-0d1d-48a3-b394-814d5b601e05")

projects = org.projects.all()
for project in projects:
  print(project.remoteRepoUrl)
  if project.remoteRepoUrl == repoUrlToDelete:
    print("deleting" + project.name)
    # project.delete()



