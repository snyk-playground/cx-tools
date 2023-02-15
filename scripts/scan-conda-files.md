# Scan Environment.yml files from Conda

## Description
Use this script to convert environment.yml files to requirements.txt and run a snyk test and monitor with --skip-unresolved switch.  This script will search down from the current directory for environment.yml.  Keep in mind that every dependency might not be found in pip from your conda file.

## Requirements
Conda needs to be installed in the environment.
Environment variable CONDA_HOME needs to be specified.  e.g. export CONDA_HOME=/Users/johndoe/miniconda3

## Script / Code Example
```
import os
import subprocess

RESULT_CONDA = []
DEFAULT_TEST_ARGS = ["snyk", "test", "--skip-unresolved"]
DEFAULT_MONITOR_ARGS = ["snyk", "monitor", "--skip-unresolved"]
DIRNAME = os.getcwd()
CONDA_FILE = ["environment.yml"]
CONDA_HOME = os.environ['CONDA_HOME']
conda_sh = CONDA_HOME + '/etc/profile.d/conda.sh'

snyk_test_args = list(DEFAULT_TEST_ARGS)
snyk_monitor_args = list(DEFAULT_MONITOR_ARGS)

if 'CONDA_HOME' in os.environ:
    print("Conda home path is the following: " + CONDA_HOME)
else:
    print("Conda home path is not set.  Please set CONDA_HOME environment variable")
    os._exit()


def findenvname(file):
    infile = open(file, 'r')
    firstline = infile.readline()
    envname = str.split(firstline)
    return envname[1]


# Find Conda files
print("Finding Conda files...")
for name in CONDA_FILE:
    for root, dirs, files in os.walk(DIRNAME):
        if name in files:
            RESULT_CONDA.append(os.path.join(root, name))


# Convert Conda files to requirements.txt and run a Snyk scan
for i in RESULT_CONDA:
    environment = findenvname(i)

    print("Environment name for conda file: " + environment)
    print("Running initializing conda bash, activate and creating environment...")
    subprocess.run("source " + conda_sh + " && conda activate && conda init bash && conda env create --name " + environment + " && conda activate " + environment, shell=True)
    print("Installing pip and converting Conda files to requirements.txt...")
    subprocess.run("source " + conda_sh + " && conda activate && conda install pip && pip list --format=freeze > requirements.txt && cat requirements.txt | xargs -n 1 pip install", shell=True)
    print("Starting Snyk monitor/test Scan...")
    subprocess.run(DEFAULT_MONITOR_ARGS)
    subprocess.run(DEFAULT_TEST_ARGS)
```
