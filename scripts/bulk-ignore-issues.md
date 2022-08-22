# Bulk ignore issues

## Description

Use this script to bulk ignore projects issues for any reason. In this example we will ignore all issues that are not fixable

## Flow and Endpoints

- Get all the issues from API
    - [Get all projects](https://apidocs.snyk.io/?version=2022-04-06%7Eexperimental#get-/orgs/-org_id-/projects)
    - [Get all issues, but code](https://snyk.docs.apiary.io/#reference/reporting-api/latest-issues/get-list-of-latest-issues)
    - [Get all code issues](https://apidocs.snyk.io/?version=2022-04-06%7Eexperimental#get-/orgs/-org_id-/issues)
- Filter the API calls with parameters
- Write a wrapper/locally store the issues for to solve iteration of bulk ignoring
- Quarterly runs to be controlled by a cron job

## Code examples

(Java Script)
```jsx
import fetch from "node-fetch";
 
const TOKEN = "";
const ORG_ID = "123";
 
type ProjectIssue = {
 projectID: string;
 issueID: string;
};
let issues: Array<ProjectIssue> = [];
 
(async function () {
 const projectsResult = await fetch(
   `https://api.snyk.io/rest/orgs/${ORG_ID}/projects?version=2022-04-06~experimental`,
   {
     method: "GET",
     headers: {
       "Content-Type": "application/json",
       Authorization: `token ${TOKEN}`,
     },
   }
 );
 
 const projectsBody = await projectsResult.json();
 const projectIDs = projectsBody.data.map((p: any) => p.id);
 
 console.log("Collect issues from each projects");
 for (const projectID of projectIDs) {
   // Only Code issues
   const projectIssuesResult = await fetch(
     `https://api.snyk.io/rest/orgs/${ORG_ID}/issues?&project_id=${projectID}&version=2022-04-06~experimental`,
     {
       method: "GET",
       headers: {
         "Content-Type": "application/json",
         Authorization: `token ${TOKEN}`,
       },
     }
   );
   const projectIssuesBody = await projectIssuesResult.json();
   const projectIssues = projectIssuesBody.data.map((issue: any) => issue.id);
   console.log("project id", projectID, projectIssues);
   projectIssues.forEach((i: any) => {
     issues.push({ projectID, issueID: i });
   });
 }
 
 // Only license, configuration and security issues
 const issuesEverythingButCodeResult = await fetch(
   "https://snyk.io/api/v1/reporting/issues/latest",
   {
     method: "POST",
     headers: {
       "Content-Type": "application/json",
       Authorization: `token ${TOKEN}`,
     },
     body: JSON.stringify({
       filters: {
         orgs: [ORG_ID],
         severity: ["critical", "high"],
         fixable: false,
       },
     }),
   }
 );
 const issuesEverythingButCodeBody = await issuesEverythingButCodeResult.json();
 const iss = issuesEverythingButCodeBody.results.map(
   (i: any): ProjectIssue => ({ projectID: i.project.id, issueID: i.issue.id })
 );
 issues = issues.concat(iss);
 console.log(issues);
 
 for (const issue of issues) {
   const ignoreResult = await fetch(
     `https://snyk.io/api/v1/org/${ORG_ID}/project/${issue.projectID}/ignore/${issue.issueID}`,
     {
       method: "POST",
       headers: {
         "Content-Type": "application/json",
         Authorization: `token ${TOKEN}`,
       },
       body: JSON.stringify({
         reason: "I do not like it",
         reasonType: "not-vulnerable",
         disregardIfFixable: false,
       }),
     }
   );
   console.log(`Issue ${issue.issueID} on project ${issue.projectID} ignored`);
 }
})();
```