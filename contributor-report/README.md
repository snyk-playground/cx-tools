# Snyk Developer Report Generation Guide

Generate comprehensive reports of developers associated with your projects, repositories, and container images across your Snyk group. This guide provides two approaches: a Python script for automated batch processing and curl commands for ad-hoc queries.

## Overview

This tool retrieves developer information from the Snyk Asset Search API, allowing you to export:

- **Project name** - The asset name in Snyk
- **Repository URL** - Where the code is hosted
- **Developer username** - The developer's username
- **Developer email** - The developer's email address
- **Organization** - The Snyk organization the asset belongs to

The data is output in CSV format, making it easy to import into spreadsheets, databases, or other tools.

## Prerequisites

- A valid Snyk API token with group-level read permissions and Inventory access
- Your Snyk Group ID (UUID format, e.g., `your-group-id-goes-here`)
- Python 3.8 or higher
- `requests` library: `pip install requests`
- For EU/AU regions, the appropriate regional API endpoint

## Setup

### Python Script

1. **Install dependencies:**

   ```bash
   pip install requests
   ```

2. **Set your API token:**

   ```bash
   export SNYK_TOKEN="your-snyk-api-token"
   ```

3. **Get your Group ID:**

   - Navigate to your Snyk organization
   - Go to Settings > General
   - Copy your Group ID

## Usage

The Python script automates the entire process with comprehensive error handling and retry logic.

### Basic Usage

```bash
python fetch_dev_report.py \
  --group-id <YOUR_GROUP_ID> \
  --output report.csv
```

#### Output to stdout

```bash
python fetch_dev_report.py \
  --group-id <YOUR_GROUP_ID>
```

#### Common Options

| Option | Description | Default |
|--------|-------------|---------|
| `--group-id` | **Required.** Your Snyk Group ID | - |
| `--token` | API token (or use `SNYK_TOKEN` env var) | `SNYK_TOKEN` |
| `--base-url` | API endpoint URL | `https://api.snyk.io/rest` |
| `--version` | API version to use | `2024-10-15` |
| `--output` | Output CSV file path or `-` for stdout | `-` (stdout) |
| `--asset-type` | Filter by asset type: `repository`, `image`, or `package` | All types |
| `--skip-empty` | Skip assets with no developers or organizations | Off |
| `--dedupe` | Remove duplicate rows | Off |
| `--timeout` | HTTP timeout in seconds | 30 |
| `--debug` | Print detailed debug information to stderr | Off |
| `--dump-first` | Print first asset payload for debugging | Off |
| `--max-assets` | Stop after processing N assets (useful for testing) | No limit |

#### Examples

**Filter to repositories only, skip empty assets:**

```bash
python fetch_dev_report.py \
  --group-id <YOUR_GROUP_ID> \
  --asset-type repository \
  --skip-empty \
  --output report.csv
```

**Debug mode with verbose output:**

```bash
python fetch_dev_report.py \
  --group-id <YOUR_GROUP_ID> \
  --debug \
  --dump-first \
  --output report.csv
```

**Deduplicate results:**

```bash
python fetch_dev_report.py \
  --group-id <YOUR_GROUP_ID> \
  --dedupe \
  --output report.csv
```

**EU region:**

```bash
python fetch_dev_report.py \
  --group-id <YOUR_GROUP_ID> \
  --base-url https://api.eu.snyk.io/rest \
  --output report.csv
```

## Regional Endpoints

If you're using a regional Snyk deployment, update the base URL accordingly:

| Region | Base URL |
|--------|----------|
| US (default) | `https://api.snyk.io/rest` |
| US2 | `https://api.us.snyk.io/rest` |
| EU | `https://api.eu.snyk.io/rest` |
| AU | `https://api.au.snyk.io/rest` |

**Python example:**

```bash
python fetch_dev_report.py \
  --group-id <YOUR_GROUP_ID> \
  --base-url https://api.eu.snyk.io/rest \
  --output report.csv
```

## Output Format

The generated CSV includes the following columns:

```text
project,repo,developer.username,developer.email,organization
My App,https://github.com/company/my-app,john.doe,john.doe@company.com,Engineering
My App,https://github.com/company/my-app,jane.smith,jane.smith@company.com,Engineering
Container Service,ghcr.io/company/service:latest,bob.johnson,bob.johnson@company.com,Platform
```

## Troubleshooting

### 401 Unauthorized

**Problem:** `HTTP 401 Client Error: Unauthorized`

**Solutions:**

1. Verify your API token is correct: `echo $SNYK_TOKEN`
2. Ensure your token has group-level read permissions and Inventory access
3. Confirm you're using the correct regional endpoint (US vs EU vs AU)
4. Verify the token hasn't expired

### 404 Not Found

**Problem:** `HTTP 404 Client Error: Not Found`

**Solutions:**

1. Verify the Group ID is correct
2. Check you're using the correct base URL for your region
3. Ensure you have access to the group with your token

### 500 Internal Server Error

**Problem:** `HTTP 500 for https://api.snyk.io/rest/groups/.../assets/search`

**Solutions:**

1. The Python script automatically retries with different API versions. This is expected behavior.
2. If the issue persists, wait a moment and retry

### Empty Results

**Problem:** Script runs but returns zero rows

**Possible causes:**

1. Assets exist but have no developers assigned in Snyk
2. Assets have no associated organization
3. Use `--debug` flag to see how many assets were processed
4. Use `--dump-first` flag to see the first asset payload structure

**Debug command:**

```bash
python fetch_dev_report.py \
  --group-id <YOUR_GROUP_ID> \
  --debug \
  --dump-first
```

### Timeout Issues

**Problem:** Script times out before completing

**Solutions:**

1. Increase timeout: `--timeout 60` (default is 30 seconds)
2. Reduce dataset size: use `--asset-type repository` to filter
3. Process in batches: use `--max-assets 100` to test on smaller subset

## Performance Tips

For large groups with many assets:

1. **Filter by asset type** to reduce the dataset:

   ```bash
   python fetch_dev_report.py \
     --group-id <YOUR_GROUP_ID> \
     --asset-type repository \
     --output report.csv
   ```

2. **Skip empty assets** to reduce processing:

   ```bash
   python fetch_dev_report.py \
     --group-id <YOUR_GROUP_ID> \
     --skip-empty \
     --output report.csv
   ```

3. **Deduplicate** if running multiple times:

   ```bash
   python fetch_dev_report.py \
     --group-id <YOUR_GROUP_ID> \
     --dedupe \
     --output report.csv
   ```

## API Details

### Endpoint

```text
POST /rest/groups/{group_id}/assets/search
```

### Query Parameters

- `version`: API version (default: `2024-10-15`)

## Support

If you encounter issues:

1. **Check the prerequisites** - Ensure all required tools and tokens are in place
2. **Run with `--debug` flag** - Get detailed information about what the script is doing
3. **Use `--dump-first`** - See the actual API response structure
4. **Verify your Group ID** - Double-check this is correct in Snyk settings
5. **Test with curl** - Try a simple curl command to verify API access

## Security Best Practices

1. **Never commit your API token** - Use environment variables or secure credential storage
2. **Rotate tokens regularly** - Follow your organization's token rotation policy
3. **Limit token scope** - Use tokens with only the necessary permissions
4. **Use regional endpoints** - Keep data within your compliance region
5. **Protect output files** - CSV files may contain email addresses; treat accordingly

## Additional Resources

- [Snyk API Documentation](https://snyk.io/docs/snyk-cli/cli-docs/snyk-api-docs/)
- [Snyk Group Settings](https://app.snyk.io/settings)
- [Asset Management in Snyk](https://docs.snyk.io/snyk-api/reference)

## Version History

**1.0.0** (2024)

- Initial release
- Asset Search API integration
- Python script with retry logic
- curl command examples
- `--skip-empty` option for filtering empty assets
