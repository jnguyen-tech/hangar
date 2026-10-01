# read_jobs.py
# Phase 4, step 1: open the jobs file and look at the first few rows.

import csv
import os

PROJECT_FOLDER = os.path.dirname(os.path.abspath(__file__))
JOBS_FILE = os.path.join(PROJECT_FOLDER, "data", "raw", "maintenance_jobs_export.csv")

file = open(JOBS_FILE, encoding="utf-8")
reader = csv.DictReader(file)

count = 0
for row in reader:
    if count < 5:
        print(row)
    count += 1

file.close()
print("Total jobs:", count)