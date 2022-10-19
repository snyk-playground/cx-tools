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

        // send data to DataDog
        StringBuilder sb = new StringBuilder();

        sb.Append("{");
        sb.Append("  \"title\": \"Snyk: " + projectName + "\",");
        sb.Append("  \"text\": \"Snyk: " + projectName + "\",");
        sb.Append("  \"tags\": [");
        sb.Append("    \"projectName:" + projectName + "\",");
        sb.Append("    \"browseUrl:" + browseUrl + "\",");
        sb.Append("    \"imageId:" + data.project.imageId + "\",");
        sb.Append("    \"imageTag:" + data.project.imageTag + "\",");
        sb.Append("    \"imagePlatform:" + data.project.imagePlatform + "\",");
        sb.Append("    \"imageBaseImage:" + data.project.imageBaseImage + "\",");
        sb.Append("    \"containerImage:" + containerImage + "\",");
        sb.Append("    \"issueCountsBySeverityLow:" + data.project.issueCountsBySeverity.low + "\",");
        sb.Append("    \"issueCountsBySeverityHigh:" + data.project.issueCountsBySeverity.high + "\",");
        sb.Append("    \"issueCountsBySeverityMedium:" + data.project.issueCountsBySeverity.medium + "\",");
        sb.Append("    \"issueCountsBySeverityCritical:" + data.project.issueCountsBySeverity.critical + "\"");
        sb.Append("  ]");
        sb.Append("}");

        string payload = sb.ToString();
        //log.LogInformation("content: " + payload);

        var content = new StringContent(payload);

        content.Headers.ContentType = new MediaTypeHeaderValue("application/json");

        var DATADOG_EVENTS_URL = Environment.GetEnvironmentVariable("DATADOG_EVENTS_URL");
        var DATADOG_API_KEY = Environment.GetEnvironmentVariable("DATADOG_API_KEY");

        var url = DATADOG_EVENTS_URL;
        using var client = new HttpClient();
        client.DefaultRequestHeaders.Add("DD-API-KEY", DATADOG_API_KEY);
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