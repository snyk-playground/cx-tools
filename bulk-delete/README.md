<h2>What is this tool for? </h2> <br>

This tool allows you to delete projects in bulk within Snyk by specifying a set of organazations and types of projects to delete<br>

<h2>Installation instructions</h2><br>

Clone this repo and run <pre><code>pip3 install -r requirements.txt</pre></code><br>

<h2>How do I use this tool? </h2><br>

Within the cloned repo run <pre><code>python3 snyk-bulk-delete.py (add flags here)</code></pre><br> add the necessary flags listed below <br>

<pre><code>
--help/-h : Returns this page \n--orgs/<br>
-o : A set of orgs upon which to perform delete (use ! for all orgs)<br>
--scatypes : Defines SCA type/s of projects to deletes <br>
--products : Defines product/s types of projects to delete(opensource,container,iac,or sast)<br>
--origins : Defines origin types of projects to delete<br>
--dryrun : Add this flag to perform a dry run of script which doesn't actually delete any projects<br>
 * Please replace spaces with dashes(-) when entering orgs <br>
 * If entering multiple values use the following format: "value-1 value-2 value-3"<br>
 * Types and origins are defined under this API > https://snyk.docs.apiary.io/#reference/projects/individual-project/retrieve-a-single-project
</code></pre>

Example where all npm and container projects are deleted within test org 1 and test org 2
<br>
<pre><code>python3 snyk-bulk-delete.py --orgs "test-org-1 test-org-2" --products container --scatypes npm
</code></pre>



