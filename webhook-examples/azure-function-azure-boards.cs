#r "Newtonsoft.Json"

using System.Net;
using Microsoft.AspNetCore.Mvc;
using Microsoft.Extensions.Primitives;
using Newtonsoft.Json;
using System.Net.Http;
using System.Net.Http.Headers;
using System.Text;
using Newtonsoft.Json.Linq;

public static async Task<IActionResult> Run(HttpRequest req, ILogger log)
{
    log.LogInformation("C# HTTP trigger function processed a request.");

    string name = req.Query["name"];

    string requestBody = await new StreamReader(req.Body).ReadToEndAsync();
    dynamic data = JsonConvert.DeserializeObject(requestBody);
    //log.LogInformation("data: " + requestBody);

    string count = data.newIssues.Count.ToString();
    string projectName = data.project.name;
    log.LogInformation("Snyk project: " + projectName);
    int idxRepoURLProject = projectName.IndexOf("/");
    string AzureDevOpsProject = projectName.Substring(0, idxRepoURLProject);
    log.LogInformation("Azure DevOps Project: " + AzureDevOpsProject);
    log.LogInformation("data.newIssues.Count: " + count);
    string responseMessage = "No new issues found. Nothing to process!";

    if (data.newIssues.Count > 0)
    {
        log.LogInformation("New issues found!");

        name = name ?? data?.name;
        string browseUrl = data.project.browseUrl;
        int x = 0;

        for (int i = 0; i < data.newIssues.Count; i++)
        {
            // send data to Azure Boards
            StringBuilder sb = new StringBuilder();
            sb.Append("[");

            //var item = (JObject)data.newIssues[i];
            //do something with item
            string id = data.newIssues[i].id.ToString();
            //log.LogInformation("data.newIssues[i].id:" + id);
            string descr = data.newIssues[i].issueData.description.ToString();
            descr = descr.Replace("\"", "'");
            //log.LogInformation("data.newIssues[i].issueData.description:" + descr);
            string snykOrgid = data.org.id.ToString();

            sb.Append("  {");
            sb.Append("    \"op\": \"add\",");
            sb.Append("    \"path\": \"/fields/System.Title\", ");
            sb.Append("    \"from\": null, ");
            sb.Append("    \"value\": \"" + id + "\"");
            sb.Append("  },");
            sb.Append("  {");
            sb.Append("    \"op\": \"add\",");
            sb.Append("    \"path\": \"/fields/System.Description\",");
            sb.Append("    \"from\": null,");
            sb.Append("    \"value\": \"" + descr + "\"");
            sb.Append("  }");
            sb.Append("]");

            string payload = sb.ToString();
            //log.LogInformation("content: " + payload);

            var content = new StringContent(payload);

            content.Headers.ContentType = new MediaTypeHeaderValue("application/json-patch+json");

            var AZURE_DEVOPS_ORG = Environment.GetEnvironmentVariable("AZURE_DEVOPS_ORG");
            var AZURE_DEVOPS_PROJECT = Environment.GetEnvironmentVariable("AZURE_DEVOPS_PROJECT");
            var AZURE_DEVOPS_USER = Environment.GetEnvironmentVariable("AZURE_DEVOPS_USER");
            var AZURE_DEVOPS_PAT = Environment.GetEnvironmentVariable("AZURE_DEVOPS_PAT");
            var AZURE_DEVOPS_API_VERSION = Environment.GetEnvironmentVariable("AZURE_DEVOPS_API_VERSION");
            var AZURE_DEVOPS_SNYKORG_BOARDS_MAPPING = Environment.GetEnvironmentVariable("AZURE_DEVOPS_SNYKORG_BOARDS_MAPPING");
            var AZURE_DEVOPS_SNYKORG_BOARDS_MAPPING_ENABLED = Boolean.Parse(Environment.GetEnvironmentVariable("AZURE_DEVOPS_SNYKORG_BOARDS_MAPPING_ENABLED"));
            //log.LogInformation("AZURE_DEVOPS_SNYKORG_BOARDS_MAPPING: " + AZURE_DEVOPS_SNYKORG_BOARDS_MAPPING);
            //log.LogInformation("AZURE_DEVOPS_SNYKORG_BOARDS_MAPPING_ENABLED: " + AZURE_DEVOPS_SNYKORG_BOARDS_MAPPING_ENABLED);

            if (AZURE_DEVOPS_SNYKORG_BOARDS_MAPPING_ENABLED)
            {
                dynamic boardsCustomMapping = JsonConvert.DeserializeObject(AZURE_DEVOPS_SNYKORG_BOARDS_MAPPING);
                JArray resources = (JArray)boardsCustomMapping;
                //log.LogInformation("snykOrgid: " + snykOrgid);
                foreach (var boardsCustomMappingItem in resources
                    .Where(obj => obj["snykOrgId"].Value<string>() == snykOrgid))
                {
                    if (boardsCustomMappingItem != null &&
                        boardsCustomMappingItem["snykOrgId"] != null)
                    {
                        string boardsCustomMappingSnykOrgId = boardsCustomMappingItem["snykOrgId"].ToString();
                        string boardsCustomMappingAzureBoardsProject = boardsCustomMappingItem["azureBoardsProject"].ToString();
                        log.LogInformation("boardsCustomMapping.snykOrgId: " + boardsCustomMappingSnykOrgId);
                        log.LogInformation("boardsCustomMapping.azureBoardsProject: " + boardsCustomMappingAzureBoardsProject);

                        AzureDevOpsProject = boardsCustomMappingAzureBoardsProject;
                    }
                }

            }

            var url = "https://dev.azure.com/" + AZURE_DEVOPS_ORG + "/" + AzureDevOpsProject + "/_apis/wit/workitems/$Issue?api-version=" + AZURE_DEVOPS_API_VERSION;
            using var client = new HttpClient();
            var authToken = Encoding.ASCII.GetBytes(AZURE_DEVOPS_USER + ":" + AZURE_DEVOPS_PAT);
            client.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Basic", Convert.ToBase64String(authToken));
            var response = await client.PostAsync(url, content);

            string result = response.Content.ReadAsStringAsync().Result;
            log.LogInformation("response.StatusCode: " + response.StatusCode);
            if (response.StatusCode == HttpStatusCode.OK)
            {
                x++;
            }
            //log.LogInformation("result: " + result);
        }

        // write output as summary
        string output = "Successfully processed " + x + " issues.";
        log.LogInformation(output);
        responseMessage = output;
    }

    return new OkObjectResult(responseMessage);
}