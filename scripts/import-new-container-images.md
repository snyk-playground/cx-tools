# Import fresh Container images

## Description

Use this script to import "fresh" container images into Snyk and/or remove/decativate "old" images from Snyk, in this example we decided that "fresh" images are younger than 6 months

## Flow and Endpoints

### Flow:

**Importing “fresh” images**

1. Get a list of all image tags and their upload time using a dedicated API from the CR, or their creation time using Docker V2 standard API
2. Filter images with upload time/creation time is shorter than what you decide as "fresh" (for example: all images that were created during the last 6 months)
3. Import relevant images using the Snyk import API

**Removing old image projects**

1. Get a list of container registry projects from snyk
2. For each project - get the image name + tag and look up in GCR api for the image upload/creation time and check if it’s greater than what you decide as "fresh"
3. For each old image - remove it using the delete project API

### Endpoints used:

[List all Snyk projects per org](https://apidocs.snyk.io/?version=2023-06-23%7Ebeta#tag--Projects) - Used for listing all GCR projects

[Import a target](https://snyk.docs.apiary.io/#reference/import-projects/import/import-targets) - Used to import a repo

[Get import status](https://snyk.docs.apiary.io/#reference/import-projects/import-job/get-import-job-details) - Used to get job status of project import job

[Delete a project](https://snyk.docs.apiary.io/#reference/projects/individual-project/delete-a-project) - To delete a project

## Code examples

(Java Script)
Architecture:

```jsx
// Get a list from Google Container Register
containers = googleContainerRegister.getContainers()
// Add each GCR to Snyk if newer than 6 months
jobIds = []
importErrors = []
for (container in containers){
	if (container.created < 6.months.ago){
		snyk.importContainer(orgId, integrationId, project, repo, tag)
			.onSuccess(jobId){
		jobIds.push(jobId)
}).onFailure(err){
importErrors.push({orgId, integrationId, project, repo, tag)
}
	}
}
// Await on successful import
while (jobIds.size > 0){
Switch (snyk.importJobDetails(orgId, integrationId, jobId)){
	Complete: 
		jobIds.pop(jobId)
	Failed:
		jobIds.pop(jobId)
		log.err(jobId)
}
}
// Part 2
// Get list of Snyk projects using `origin` query param No enum
projects = snyk.getProjects(origin: “GCR”)
// For each project, if `created` date is older than 1 day from today, then delete project (orgId, projectId)
forEach (project in projects){
	If (project.created < today() - 1){
		snyk.deleteProject(orgId, project.id)
}
}
```

```jsx
import fetch from "node-fetch";
const orgId = "FAKE_ORG_ID";
const integrationId = "FAKE_INTEGRATION_ID";
const authToken = "FAKE_AUTH_TOKEN";
const WAIT_IN_BETWEEN_TRIES_MS = 5000;
 
const importImage = async (project, repo, tag) => {
 var body = {
   target: {
     name: `${project}/${repo}:${tag}`,
   },
 };
 
 const result = await fetch(
   `https://snyk.io/api/v1/org/${orgId}/integrations/${integrationId}/import`,
   {
     method: "POST",
     headers: {
       "Content-Type": "application/json; charset=utf-8",
       Authorization: `token ${authToken}`,
     },
     body: JSON.stringify(body),
   }
 );
 
 if (result.status !== 201) {
   console.log(`Failed ${project}/${repo}:${tag}`);
 }
 
 return result.status === 201 ? result.headers.get("location") : null;
};
 
const getImportJobStatus = async (imageJobLocation) => {
 const result = await fetch(imageJobLocation, {
   method: "GET",
   headers: {
     "Content-Type": "application/json; charset=utf-8",
     Authorization: `token ${authToken}`,
   },
 });
 return result.json();
};
 
const listAllGcrProjectsOverXMillisecondsOld = async (numberOfMs) => {
  let allProjects = []
  let nextPage = `/orgs/${orgId}/projects?version=2023-06-23&limit=100&origins=GCR`
  
  while(nextPage){
   let response = await fetch(`https://api.snyk.io/rest${nextPage}&origins=GCR`, {
   method: "GET",
   headers: {
     "Content-Type": "application/json; charset=utf-8",
     Authorization: `token ${authToken}`,
      },
    });
    response = await response.json()
    allProjects.push(response.data)
    if (response.links.next != undefined){
      nextPage = response.links.next
    }else{
      nextPage = undefined
    }
  }

  return allProjects[0].filter(
    (project) =>
      new Date().getTime() - new Date(project.attributes.created).getTime() >
      1000 * 60 * 60 * 24
  ).map((project) => project.id);
};
 
const deleteProject = async (projectId) => {
 const result = await fetch(
   `https://snyk.io/api/v1/org/${orgId}/project/${projectId}`,
   {
     method: "DELETE",
     headers: {
       "Content-Type": "application/json; charset=utf-8",
       Authorization: `token ${authToken}`,
     },
   }
 );
 
 console.log(result.status, await result.json());
 return result.status === 200;
};
 
const run = async () => {
 const images = [
   {
     project: "project-name",
     repository: "repository-name",
     tag: "image-tag",
   },
 ];
 
 images.forEach(async (image) => {
   console.log(`Importing ${image.project}/${image.repository}:${image.tag}`);
   const imageJobLocation = await importImage(
     image.project,
     image.repository,
     image.tag
   );
 
   let importJobStatus = await getImportJobStatus(imageJobLocation);
   while (importJobStatus.status === "pending") {
     console.log(
       "Retrying until job complete. Completed imports:",
       importJobStatus.logs.filter((log) => log.status !== "pending").length,
       "/",
       importJobStatus.logs.length
     );
     await new Promise((resolve) =>
       setTimeout(resolve, WAIT_IN_BETWEEN_TRIES_MS)
     );
     importJobStatus = await getImportJobStatus(imageJobLocation);
   }
   console.log(importJobStatus);
 });
 
 const projectsToDeleteIds = await listAllGcrProjectsOverXMillisecondsOld(1000 * 60 * 60 * 24);
 console.log(`Deleting ${projectsToDeleteIds.length} projects: ${projectsToDeleteIds}`
 );
 await Promise.all(projectsToDeleteIds.map((id) => deleteProject(id)));
};
run();
```