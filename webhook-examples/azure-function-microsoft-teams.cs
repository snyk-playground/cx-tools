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
    log.LogInformation("data.newIssues.Count: " + count);
    string responseMessage = "No new issues found. Nothing to process!";

    if (data.newIssues.Count > 0)
    {
        log.LogInformation("New issues found!");

        name = name ?? data?.name;
        string projectName = data.project.name;
        string browseUrl = data.project.browseUrl;
        int x = 0;

        for (int i = 0; i < data.newIssues.Count; i++)
        {
            // send data to Azure Boards
            StringBuilder sb = new StringBuilder();

            //var item = (JObject)data.newIssues[i];
            //do something with item
            string id = data.newIssues[i].id.ToString();
            //log.LogInformation("data.newIssues[i].id:" + id);
            string descr = data.newIssues[i].issueData.description.ToString();
            //log.LogInformation("data.newIssues[i].issueData.description:" + descr);

            sb.Append("{");
            sb.Append("  \"@context\": \"https://schema.org/extensions\",");
            sb.Append("  \"@type\": \"MessageCard\",");
            sb.Append("  \"themeColor\": \"0072C6\",");
            sb.Append("  \"title\": \"" + projectName + "\",");
            sb.Append("  \"text\": \"" + id + "<br><br>" + descr + "\",");
            sb.Append("  \"potentialAction\": [ ");
            sb.Append("    {");
            sb.Append("      \"@type\": \"OpenUri\",");
            sb.Append("      \"name\": \"Project Details\",");
            sb.Append("      \"targets\": [");
            sb.Append("        { \"os\": \"default\", \"uri\": \"" + browseUrl + "\" }");
            sb.Append("      ]");
            sb.Append("    }");
            sb.Append("  ]");
            sb.Append("}");

            string payload = sb.ToString();
            //log.LogInformation("content: " + payload);

            var content = new StringContent(payload);

            content.Headers.ContentType = new MediaTypeHeaderValue("application/json");

            var MS_TEAMS_WEBHOOK = Environment.GetEnvironmentVariable("MS_TEAMS_WEBHOOK");
            var url = MS_TEAMS_WEBHOOK;
            using var client = new HttpClient();
            var response = await client.PostAsync(url, content);

            string result = response.Content.ReadAsStringAsync().Result;
            //log.LogInformation("response.StatusCode: " + response.StatusCode);
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