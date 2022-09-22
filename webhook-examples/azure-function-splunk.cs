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

    string responseMessage = "No valid payload received!";
    if (data.project != null)
    {
        int x = 1;
        string count = data.newIssues.Count.ToString();
        string projectName = data.project.name;
        string[] projectNameParts = projectName.Split(':');
        string containerImage = projectName;
        if (projectNameParts.Length > 0)
        {
            containerImage = projectNameParts[1] + ":" + data.project.imageTag;
        }
        log.LogInformation(projectName + ", data.newIssues.Count: " + count);
        responseMessage = "No new issues found. Nothing to process!";

        name = name ?? data?.name;
        string browseUrl = data.project.browseUrl;

        StringBuilder sbDimensions = new StringBuilder();
        sbDimensions.Append("      , \"dimensions\": {");
        sbDimensions.Append("        \"projectName\": \"" + projectName + "\",");
        sbDimensions.Append("        \"browseUrl\": \"" + browseUrl + "\",");
        sbDimensions.Append("        \"imageId\": \"" + data.project.imageId + "\",");
        sbDimensions.Append("        \"imageTag\": \"" + data.project.imageTag + "\",");
        sbDimensions.Append("        \"imagePlatform\": \"" + data.project.imagePlatform + "\",");
        sbDimensions.Append("        \"imageBaseImage\": \"" + data.project.imageBaseImage + "\",");
        sbDimensions.Append("        \"containerImage\": \"" + data.project.imageBaseImage + "\"");
        sbDimensions.Append("      }");

        // send data to Splunk
        StringBuilder sb = new StringBuilder();
        sb.Append("{");
        sb.Append("  \"gauge\": [");
        sb.Append("    {");
        sb.Append("      \"metric\": \"Snyk.issueCountsBySeverityLow\",");
        sb.Append("      \"value\": " + data.project.issueCountsBySeverity.low + "");
        sb.Append(sbDimensions.ToString());
        sb.Append("    },");
        sb.Append("    {");
        sb.Append("       \"metric\": \"Snyk.issueCountsBySeverityHigh\",");
        sb.Append("       \"value\": " + data.project.issueCountsBySeverity.high + "");
        sb.Append(sbDimensions.ToString());
        sb.Append("    },");
        sb.Append("    {");
        sb.Append("      \"metric\": \"Snyk.issueCountsBySeverityMedium\",");
        sb.Append("      \"value\": " + data.project.issueCountsBySeverity.medium + "");
        sb.Append(sbDimensions.ToString());
        sb.Append("    },");
        sb.Append("    {");
        sb.Append("      \"metric\": \"Snyk.issueCountsBySeverityCritical\",");
        sb.Append("      \"value\": " + data.project.issueCountsBySeverity.critical + "");
        sb.Append(sbDimensions.ToString());
        sb.Append("    }");
        sb.Append("  ]");
        sb.Append("}");

        string payload = sb.ToString();
        //log.LogInformation("content: " + payload);

        var content = new StringContent(payload);

        content.Headers.ContentType = new MediaTypeHeaderValue("application/json");

        var SPLUNK_EVENTS_URL = Environment.GetEnvironmentVariable("SPLUNK_EVENTS_URL");
        var SPLUNK_ACCESS_TOKEN = Environment.GetEnvironmentVariable("SPLUNK_ACCESS_TOKEN");

        var url = SPLUNK_EVENTS_URL;
        using var client = new HttpClient();
        client.DefaultRequestHeaders.Add("X-SF-TOKEN", SPLUNK_ACCESS_TOKEN);
        var response = await client.PostAsync(url, content);

        string result = response.Content.ReadAsStringAsync().Result;
        log.LogInformation("response.StatusCode: " + response.StatusCode);
        if (response.StatusCode == HttpStatusCode.OK)
        {
            x++;
        }
        //log.LogInformation("result: " + result);

        // write output as summary
        string output = "Successfully processed " + x + " issues.";
        log.LogInformation(output);
        responseMessage = output;
    }
    else
    {
        log.LogInformation("No project found!");
    }

    return new OkObjectResult(responseMessage);
}