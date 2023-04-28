<h2>What is this tool for? </h2> <br>

This tool allows you to delete projects in bulk within Snyk by specifying a set of organazations and types of projects to delete<br>

<h2>Installation instructions</h2><br>

Clone this repo and run <pre><code>pip3 install -r requirements.txt</pre></code><br>

<h2>How do I use this tool? </h2><br>

Set your snyk token with <pre><code>export SNYK_TOKEN=TOKEN-GOES-HERE</code></pre><br>

Within the cloned repo run <pre><code>python3 snyk-bulk-delete.py (add flags here)</code></pre><br> add the necessary flags listed below <br>

PROJECTS ARE DE-ACTIVATED BY DEFAULT AND NO ACTIONS ARE APPLIED UNLESS --FORCE FLAG IS USED, SEE DETAILS BELOW<br>
<pre><code>
--help : Returns this page \n--orgs/<br>
--orgs : A set of orgs upon which to perform delete, be sure to use org slug instead of org display name (use ! for all orgs)<br>
--sca-types : Defines SCA type/s of projects to deletes <br>
--products : Defines product/s types of projects to delete(opensource,container,iac,or sast)<br>
--delete : By default this script will deactivate projects, add this flag to delete active projects instead<br>
--delete-non-active-projects : By default this script will deactivate projects, add this flag to delete non-active projects instead (if this flag is active no active projects will be deleted)<br>
--force : By default this script will perform a dry run, add this flag to apply actions<br>
--origins : Defines origin types of projects to delete<br>
--delete-empty-orgs : This will delete all orgs that do not have any projects in them<br>
 * Please replace spaces with dashes(-) when entering orgs <br>
 * If entering multiple values use the following format: "value-1 value-2 value-3"<br>
 * Types and origins are defined under this API > https://snyk.docs.apiary.io/#reference/projects/individual-project/retrieve-a-single-project
</code></pre>

Example where all opensource npm and gradle projects from github are deleted within test-org-1 and test-org-2
<br>
<pre><code>python3 snyk-bulk-delete.py --orgs "test-org-1 test-org-2" --products opensource --sca-types "npm gradle" --origins github
</code></pre>



