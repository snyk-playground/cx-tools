# How to Scan All Projects by File Type

## When is this useful?
Useful when targeting snyk scans to a subset of (or all) projects in a monorepo. This can include Gradle projects, or other ecosystems where Snyk CLI is preferred over SCM, or to overcome challenges scanning monorepos in CI/CD with --all-projects.

## What does it do?
Recurses through directory structure looking for files to test or monitor.

- Individual test results are grouped in the UI by the top level folder name
- project names include their path within the repo
- similar grouping structure to SCM-based projects

### Windows Shell Example
looking for all gradle or yarn projects

```
@echo off
FOR %%f IN ("%CD%") DO SET GROUP=%%~nxf

SETLOCAL ENABLEDELAYEDEXPANSION
FOR %%G IN (build.gradle, yarn.lock) DO (
  FOR /f "delims=" %%A in ('forfiles /s /m *%%G /c "cmd /c echo @relpath"') DO (
    SET P=%%A
    ECHO !P!
    snyk-win monitor --file=%%A --insecure --project-name=!P:.\\=! --remote-repo-url=!GROUP!
  )
)
```

### BASH Example
GitHub - https://github.com/snyk-tech-services/snyk-scan.sh
