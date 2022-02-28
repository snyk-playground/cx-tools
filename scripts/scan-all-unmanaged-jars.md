# How to Scan all unmanaged JARs

## Description:
Snyk CLI is able to scan unmanaged JAR files in Java applications, identify their package name and version and any vulnerabilities IF the JAR file is the same as one hosted in Maven central. Java apps tend to have JAR files in a number of locations within an application, but moreover, R&D has advised us that even scanning multiple JARs in the same folder can lead to problems and instead scans of individual JAR files are preferred, especially for old Java apps that use Ant

### Steps to reproduce:
- Pre-requisites: Please note that this functionality requires at least Maven 3.1.0 to be installed alongside Snyk CLI (we require on maven-dependency-plugin 2.2 or higher)

Snyk CLI can look through JAR files in a single folder to match any dependencies hosted on Maven central using snyk test —scan-all-unmanaged command. However, R&D has advised that this functionality may be problematic, especially if the target JAR collection was not generated using a centralized dependency management tool like Maven or Gradle (for example, old apps that use Ant) ****since Snyk tries to build a maven file behind the scenes and do a "mvn install" to get a full list of transitive dependencies. Scanning multiple arbitrary JARs using snyk test —scan-all-unmanaged command, may create version conflicts or completely incompatible dependency trees that will result in errors.

It is therefore best to test each JAR file individually using snyk test —scan-unmanaged —file=/path/to/file. Testing each JAR file individually will also have a side-effect of Snyk Web UI showing the name of the JAR file that was scanned, while running a scan using —scan-all-unmanaged doesn't do that. In order to find and test JAR files in all sub-folders of an application a simple wrapper is required. Results can then be grouped in Snyk UI using ```***—remote-repo-url=***AppName argument.``` However, there may be a potential limit of 500 JARs (still being investigated as of May 14, 2020). If you run into this, you may need to adjust scripts below to use several different remote-repo-urls. For example, based on the sub-folder where a particular JAR resides.

Here is a Linux/Mac BASH script that will iterate through all subfolders starting with the current folder and test each individual JAR file. PROJECT_NAME_HERE part in —remote-repo-url is important as it'll help combine multiple scan results under a single Snyk project in the UI

```
find . -type f -name '*.jar' | uniq | xargs -I {} snyk monitor --file={} --scan-unmanaged --remote-repo-url=PROJECT_NAME_HERE
```

And here's a Windows Batch script. The customer will need to save this in a scanjar.bat file on their end (it's much easier to share this as text vs a ready made batch file due to anti-virus rules). Please see below for usage information

```
REM Usage: <this_bat_file> <PATH_TO_APP_ROOT_FOLDER> <PROJECT_NAME_FOR_SNYK>
REM For example: scanjar.bat "C:\\workspace\\app" "myapp"
SET workspace=%1
SET appname=%2
for /R %workspace% %%f in (*.jar) do cmd /c snyk monitor --scan-unmanaged --remote-repo-url=%appname% --file=%%f
```

Repo example:  https://github.com/snyk-schmidtty/altoroj-jar/tree/master/WEB-INF/lib
