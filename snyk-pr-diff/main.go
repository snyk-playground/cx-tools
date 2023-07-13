package main

import (
	"encoding/json"
	"fmt"
	"io/ioutil"
	"log"
	"os"
	"path/filepath"
	"strings"
)

func main() {
	// Check if there are at least two arguments
	if len(os.Args) < 4 {
		log.Fatal("Usage: go run main.go <code/iac> <baseline_file.json> <pr_file.json>")
	}

	// Get the product type
	productType := filepath.Clean(os.Args[1])
	productType = strings.ToUpper(productType)
	if productType != "IAC" && productType != "CODE" {
		log.Fatalf("Please set the first parameter to the product type of CODE or IAC")
	}

	// Read the baseline JSON file
	baselineFile := filepath.Clean(os.Args[2])
	baselineJSON, err := ioutil.ReadFile(baselineFile)
	if err != nil {
		log.Fatalf("Failed to read the baseline JSON file: %v", err)
	}

	// Read the PR JSON file
	prFile := filepath.Clean(os.Args[3])
	prJSON, err := ioutil.ReadFile(prFile)
	if err != nil {
		log.Fatalf("Failed to read the PR JSON file: %v", err)
	}

	// Parse the Baseline JSON scan
	var baselineData interface{}
	err = json.Unmarshal(baselineJSON, &baselineData)
	if err != nil {
		log.Fatalf("Failed to parse the Baseline JSON scan: %v", err)
	}

	// Parse the PR JSON scan
	var prData interface{}
	err = json.Unmarshal(prJSON, &prData)
	if err != nil {
		log.Fatalf("Failed to parse the PR JSON scan: %v", err)
	}

	fmt.Printf("\n")
	fmt.Printf("Running %s PR Diff \n", productType)
	fmt.Printf("\n")

	// Extract the "results" array from the Baseline scan
	baselineResults, ok := extractResults(baselineData, productType)
	if !ok {
		log.Fatal("Failed to extract 'results' from the Baseline scan")
	}

	// Extract the "results" array from the PR scan
	prResults, ok := extractResults(prData, productType)
	if !ok {
		log.Fatal("Failed to extract 'results' from PR scan")
	}

	// Find the indices of new Identifier from the PR results
	newIndices := findNewIdentifierIndices(baselineResults, prResults)

	// Extract the new issues objects from the PR results
	newIssues := extractNewIssues(prResults, newIndices)

	// Count the number of new issues found from the PR results
	issueCount := len(newIssues)

	switch productType {
		case "IAC":
			// Output the new issues from the PR results for IaC
			for _, result := range newIssues {
				severity, title, info, rule, path, file, resolve := extractIacIssueData(result)
				severity = strings.Replace(severity, "low", "Low", 1)
				severity = strings.Replace(severity, "medium", "Medium", 1)
				severity = strings.Replace(severity, "high", "High", 1)
				severity = strings.Replace(severity, "critical", "Critical", 1)
				fmt.Printf("[%s] ", severity)
				fmt.Printf("%s \n", title)
				fmt.Printf("Info: %s\n", info)
				fmt.Printf("Rule: %s\n", rule)
				fmt.Printf("File: %s\n", file)
				fmt.Printf("Path: %s\n", path)
				fmt.Printf("Resolve: %s\n", resolve)
				fmt.Printf("\n")
			}
		case "CODE":
			// Output the new issues from the PR results for Code
			for _, result := range newIssues {
				level, message, uri, startLine := extractCodeIssueData(result)
				level = strings.Replace(level, "note", "Low", 1)
				level = strings.Replace(level, "warning", "Medium", 1)
				level = strings.Replace(level, "error", "High", 1)
				fmt.Printf("✗ Severity: [%s]\n", level)
				fmt.Printf("Path: %s\n", uri)
				fmt.Printf("Start Line: %d\n", startLine)
				fmt.Printf("Message: %s\n", message)
				fmt.Printf("\n")
			}
	}

	// Output the count new issues found from the PR results
	if issueCount > 0 {
		fmt.Printf("\n")
		fmt.Printf("Total issues found: %d\n", issueCount)

		// Replace the "results" array in the PR scan with only the new issues found
		replaceResults(prData, newIssues)

		// Convert the new PR data to JSON
		updatedPRScan, err := json.Marshal(prData)
		if err != nil {
			log.Fatalf("Failed to convert updated data to JSON: %v", err)
		}

		// Write the updated PR diff scan to a file
		err = ioutil.WriteFile("snyk_pr_diff_scan.json", updatedPRScan, 0644)
		if err != nil {
			log.Fatalf("Failed to write updated data to file: %v", err)
		}

		fmt.Printf("\n")
		fmt.Println("Results saved in snyk_pr_diff_scan.json")
		os.Exit(1)
	}

	fmt.Printf("\n")
	fmt.Println("No issues found!")
}

func extractResults(data interface{}, productType string) ([]interface{}, bool) {
	switch productType {
		case "IAC":
			switch v := data.(type) {
				// Multiple IaC Files
				case []interface{}:
					var infraIssuesArr []interface{}
					for _, obj := range v {
						if targetFilePath, ok := obj.(map[string]interface{})["targetFilePath"].(string); ok {
							if infraIssues, ok := obj.(map[string]interface{})["infrastructureAsCodeIssues"].([]interface{}); ok {
								for _, issue := range infraIssues {
									if issueMap, ok := issue.(map[string]interface{}); ok {
										issueMap["targetFilePath"] = targetFilePath
									}
								}
								infraIssuesArr = append(infraIssuesArr, infraIssues...)
							}
						}
					}
					if len(infraIssuesArr) > 0 {
						return infraIssuesArr, true
					}
				// Single IaC File
				case map[string]interface{}:
					if targetFilePath, ok := v["targetFilePath"].(string); ok {
						if infraIssuesArr, ok := v["infrastructureAsCodeIssues"].([]interface{}); ok && len(infraIssuesArr) > 0 {
							for _, issue := range infraIssuesArr {
								if issueMap, ok := issue.(map[string]interface{}); ok {
									issueMap["targetFilePath"] = targetFilePath
								}
							}
							return infraIssuesArr, true
						}
					}
			}
			return nil, false
		case "CODE":
			switch v := data.(type) {
				case map[string]interface{}:
					if runs, ok := v["runs"].([]interface{}); ok && len(runs) > 0 {
						if codeResultsArr, ok := runs[0].(map[string]interface{})["results"].([]interface{}); ok {
							return codeResultsArr, true
						}
					}
			}
			return nil, false
		}
		return nil, false
}

// Find the indices of the new identifiers in the PR results array
func findNewIdentifierIndices(baselineResults, prResults []interface{}) []int {
	var newIndices []int

	for i, prResult := range prResults {
		prObject := prResult.(map[string]interface{})
		// Code Identifier Found.
		if prFingerprints, ok := prObject["fingerprints"].(map[string]interface{}); ok {
			matchFound := false
			for _, baselineResult := range baselineResults {
				baselineObject := baselineResult.(map[string]interface{})
				if baselineFingerprints, ok := baselineObject["fingerprints"].(map[string]interface{}); ok {
					// Ignore the "identity" key
					delete(baselineFingerprints, "identity")
					delete(prFingerprints, "identity")

					match := false
					if len(baselineFingerprints) == 0 && len(prFingerprints) == 0 {
						match = true
					} else {
						match = fmt.Sprint(prFingerprints) == fmt.Sprint(baselineFingerprints)
					}

					if match {
						matchFound = true
						break
					}
				}
			}
			if !matchFound {
				newIndices = append(newIndices, i)
			}
		} else if msg, ok := prObject["msg"].(string); ok {
			//IAC Identifier found. Matching on resource type, name, and issue.
			matchFound := false
			if len(msg) > 0 {
				for _, baselineResult := range baselineResults {
					baselineObject := baselineResult.(map[string]interface{})
					if baselineMsg, ok := baselineObject["msg"].(string); ok {
						if prMsg, ok := prObject["msg"].(string); ok {
							match := false
							if len(baselineMsg) == 0 && len(prMsg) == 0 {
								match = true
							} else {
								match = fmt.Sprint(prMsg) == fmt.Sprint(baselineMsg)
							}
							if match {
								matchFound = true
								break
							}
						}
					}
				}
			}
			if !matchFound {
            	newIndices = append(newIndices, i)
           	}
		}
	}

	return newIndices
}

// Extract new issues objects from the PR "results" array
func extractNewIssues(results []interface{}, indices []int) []interface{} {
	var newIssues []interface{}

	for _, idx := range indices {
		newIssues = append(newIssues, results[idx])
	}

	return newIssues
}

// Replace the "results" array in the PR data with the new issues
func replaceResults(data interface{}, newIssues []interface{}) {
	switch v := data.(type) {
	case []interface{}:
		if len(v) > 0 {
			if prData, ok := v[0].(map[string]interface{}); ok {
				prData["results"] = newIssues
			}
		}
	case map[string]interface{}:
		v["results"] = newIssues
	}
}

// Extract new Code issue data from the results to output to the console
func extractCodeIssueData(result interface{}) (string, string, string, int) {
	resultObj := result.(map[string]interface{})
	level := resultObj["level"].(string)
	message := resultObj["message"].(map[string]interface{})["text"].(string)
	locations := resultObj["locations"].([]interface{})
	uri := locations[0].(map[string]interface{})["physicalLocation"].(map[string]interface{})["artifactLocation"].(map[string]interface{})["uri"].(string)
	startLine := locations[0].(map[string]interface{})["physicalLocation"].(map[string]interface{})["region"].(map[string]interface{})["startLine"].(float64)
	return level, message, uri, int(startLine)
}

// Extract new IaC issue data from the results to output to the console
func extractIacIssueData(result interface{}) (string, string, string, string, string, string, string) {
	resultObj := result.(map[string]interface{})
	severity := resultObj["severity"].(string)
	rule := resultObj["documentation"].(string)
	path := resultObj["msg"].(string)
	file := resultObj["targetFilePath"].(string)
	iacDescription := resultObj["iacDescription"].(map[string]interface{})
	info := iacDescription["issue"].(string)
	title := resultObj["title"].(string)
	resolve := resultObj["resolve"].(string)
	return severity, title, info, rule, path, file, resolve
}
