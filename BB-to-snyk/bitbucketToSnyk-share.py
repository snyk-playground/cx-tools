#Copyright 2022 Citrix Systems
#
#Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
#
#The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
#
#THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

# Scans our Bitbucket repos and imports it to Snyk for monitoring.
# If a repo cannot be added to Snyk, it will be logged in the log file
#
# requires:
#    pip install stashy
#    pip install requests
#
# assumes:
#    Python 3 is installed
#
####
#    FAILSAFE is set in addToSnyk() to prevent clobbering Snyk. Remove this for when you want to do the real thing
#    I recommend this if you do not want to clobber Snyk with all the projects and repos for testing purposes
#    Depending on the number of repos/projects, this can take time to run (I have seen it take several minutes).
####


import os
import stashy
import json
import requests
import logging


g_configDict = {}
g_headers = {}
g_jobList = []
SNYK_BASE_ORG_URL = "https://snyk.io/api/v1/org/"


#
#
def main():
    global g_headers
    if getConfig():
        g_headers = {'content-type': 'application/json; charset=utf-8', 'Authorization': 'token ' + g_configDict['snyk_api_token']}
        addToSnyk()
        if g_jobList:
            saveJobsStatusToFile()
    else:
        exit("Unable to get config file or it is not configured correctly")


#
#
def saveJobsStatusToFile():
    try:
        with open("SnykJobStatus.json", mode="w") as jobStatus:
            json.dump(g_jobList, jobStatus)
    except:
        logging.error("Unable to write Snyk job status to file")


#
#
def getConfig():
    global g_configDict

    g_configDict = {
        "bitbucket_token": "your-bitbucket-token",
        "snyk_api_token": "your-snyk-api-token",
        "template_snyk_org": "snyk-org-id",
    }

    return(True)


#
#
def getGroupId():
    # GET https://snyk.io/api/v1/orgs add auth token this gets all orgs and the group id is orgs[n]group['id']
    try:
        result = requests.get('https://snyk.io/api/v1/orgs', headers=g_headers)
    except:
        logging.error("Unable to get group ID: " + str(result.status_code))
        exit(1)
    if result.status_code >= 400:
        logging.warn("request failed: " + str(result.status_code))

    result = json.loads(result.text)
    # result['orgs'][0]['group']['id'] group id will be the same for everything so grab the first one
    return(result['orgs'][0]['group']['id'])


#
#
def getSnykOrgs():
    '''
    get and store all Snyk orgs
    '''
    # GET https://snyk.io/api/v1/orgs
    try:
        result = requests.get('https://snyk.io/api/v1/orgs', headers=g_headers)
    except:
        print("request failed: " + str(result.status_code))
        logging.warn("request failed: " + str(result.status_code))
        return("")
    if result.status_code >= 400:
        print("request failed: " + str(result.status_code))
        logging.warn("request failed: " + str(result.status_code))

    orgDict = json.loads(result.text)
    return(orgDict)


#
#
def getBitbucketRepo(project):
    global g_configDict
    stash = stashy.client.Stash("https://YOUR.BITBUCKET.SERVER.DOMAIN/", token=g_configDict['bitbucket_token'])
    bitbucketProjects = stash.projects[project].repos.list()
    projectList = []
    for proj in bitbucketProjects:
        projKeys = stash.projects[proj['project']['key']]
        projectList.append({
            'key': proj['project']['key'],
            'name': proj['name'],
            'slug': proj['slug']
        })
    return(projectList)


#
#
def getBitbucketProjects():
    global g_configDict
    stash = stashy.client.Stash("https://YOUR.BITBUCKET.SERVER.DOMAIN/", token=g_configDict['bitbucket_token'])
    bitbucketProjects = stash.projects.list()
    return(bitbucketProjects)


#
#
def createSnykOrg(groupId, orgName):
    url = "https://snyk.io/api/v1/group/" + groupId + "/org"
    # POST https://snyk.io/api/v1/group/id/org
    try:
        result = requests.post(url, headers=g_headers, json={'name': orgName, 'sourceOrgId': g_configDict['template_snyk_org']})
    except:
        logging.warn("Create Org failed: " + str(result.status_code))
    if result.status_code >= 400:
        logging.warn("Create Org failed: " + str(result.status_code))


#
#
def getOrg(orgName, snykOrgs):
    for org in snykOrgs:
        if orgName == org['name']:
            return org
    return False


#
#
def getOrgId(orgName):
    orgDict = getSnykOrgs()
    for org in orgDict['orgs']:
        if org['name'] == orgName:
            return org['id']
    return None


#
#
def getIntegrationId(orgId):
    url = "https://snyk.io/api/v1/org/" + orgId + "/integrations/bitbucket-server"
    try:
        result = requests.get(url, headers=g_headers)
    except:
        logging.error("Unable to create an integration for: " + orgId + "  " + str(result.status_code))
        exit(1)

    if result.status_code >= 400:
        integrationId = ''
    else:
        integrationId = json.loads(result.text)['id']
    return integrationId


#
#
def newSnykOrg(orgName):
    groupId = getGroupId()
    createSnykOrg(groupId, orgName)
    orgId = getOrgId(orgName)
    integrationId = getIntegrationId(orgId)
    logging.info("Created Snyk Org: " + orgName + " " + orgId)
    return orgId, integrationId


#
#
def getOrCreateOrgIds(snykOrgs, orgName):
    org = getOrg(orgName, snykOrgs['orgs'])
    if org:
        orgId = org['id']
        integrationId = getIntegrationId(org['id'])
        logging.info("Snyk Org already exists: " + orgName + " " + orgId)
    else:
        orgId, integrationId = newSnykOrg(orgName)
    return orgId, integrationId


#
#
def getSnykOrgProjectNames(orgId):
    url = 'https://snyk.io/api/v1/org/' + orgId + '/projects'
    result = requests.get(url, headers=g_headers)
    projects = json.loads(result.text)['projects']
    projectNames = []
    for project in projects:
        projectName = project['name'].split(':')[0]
        if projectName not in projectNames:
            projectNames.append(projectName)
    return projectNames


#
#
def saveJobId(location, orgId, integrationId):
    global g_jobList
    jobId = location.split("/")[-1]
    for job in g_jobList:
        if jobId == job['job']:
            return()

    jobOrg = {'job': jobId, 'org': orgId, 'integrationId': integrationId}
    g_jobList.append(jobOrg)


#
#
def importBbRepo(repo, orgId, integrationId):
    url = SNYK_BASE_ORG_URL + orgId + '/integrations/' + integrationId + '/import'
    json = {
        'target': {
            'projectKey': repo['key'],
            'name': repo['name'],
            'repoSlug': repo['slug']
        }
    }
    try:
        result = requests.post(url, headers=g_headers, json=json)
    except:
        logging.warning("Import repo failed: " + str(result.status_code))
    if result.status_code != 201:
        logging.warning("Import repo failed: " + repo['name'] + ".  Status: " + str(result.status_code))
    else:
        logging.info("Imported repo: " + repo['key'] + " " + repo['name'])
        saveJobId(result.headers['Location'], orgId, integrationId)


#
#
def addToSnyk():
    # REMOVE FOR PRODUCTION
    # FAILSAFE = 0

    snykOrgs = getSnykOrgs()
    bbProjects = getBitbucketProjects()
    SNYK_BASE_ORG_URL = "https://snyk.io/api/v1/org/"

    for bb_project in bbProjects:

        # REMOVE FOR PRODUCTION
        # FAILSAFE += 1
        # if FAILSAFE > 6:
        #    return()

        orgName = bb_project['key'] + ": " + bb_project['name']
        orgId, integrationId = getOrCreateOrgIds(snykOrgs, orgName)

        snykProjectNames = getSnykOrgProjectNames(orgId)
        repos = getBitbucketRepo(bb_project['key'])
        for repo in repos:
            importBbRepo(repo, orgId, integrationId)


#
#
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s::%(levelname)s::%(message)s', handlers=[logging.StreamHandler()])
    main()
