# cleaning.py
# Phase 4: functions that clean the raw data, one problem at a time.

import csv
import os
from datetime import datetime

PROJECT_FOLDER = os.path.dirname(os.path.abspath(__file__))
RAW_FOLDER = os.path.join(PROJECT_FOLDER, "data", "raw")


def parse_date(text):
    """Turn a date written in any of the 4 formats in the raw data into a real date.

    Returns None if the text is blank.
    """
    text = text.strip()
    if text == "":
        return None

    if "/" in text:
        date_format = "%m/%d/%Y"          # 02/03/2025
    elif len(text) == 8 and text.isdigit():
        date_format = "%Y%m%d"            # 20250316
    elif text[4] == "-":
        date_format = "%Y-%m-%d"          # 2024-02-04
    else:
        date_format = "%d-%b-%Y"          # 29-Jul-2024

    return datetime.strptime(text, date_format).date()

def clean_job_id(text):
    """Fix job IDs written with a space (JOB 0034290) so they match the dash form (JOB-0034290)."""
    return text.strip().upper().replace(" ", "-")


def clean_depot(text):
    """Turn every spelling of a depot name into one standard name."""
    text = text.strip().upper()
    if text == "" or text == "UNK":
        return "UNKNOWN"
    if not text.endswith(" ALC"):
        text = text + " ALC"
    return text


def clean_status(text):
    """Reduce the raw statuses to the two the tracker uses: closed or open."""
    text = text.strip().upper()
    if text == "CLOSED" or text == "COMP":
        return "closed"
    return "open"

if __name__ == "__main__":
    # Test 1: one example of each format. All four should print as 2024-07-29.
    print(parse_date("2024-07-29"))
    print(parse_date("07/29/2024"))
    print(parse_date("20240729"))
    print(parse_date("29-Jul-2024"))

    # Test 2: parse every date in the jobs file and count them.
    file = open(os.path.join(RAW_FOLDER, "maintenance_jobs_export.csv"), encoding="utf-8")
    reader = csv.DictReader(file)
    date_columns = ["open_date", "original_target_date", "current_target_date", "actual_completion_date"]
    parsed = 0
    for row in reader:
        for column in date_columns:
            parse_date(row[column])
            parsed += 1
    file.close()
    print("Dates parsed:", parsed)

    # Test 3: clean the IDs, depots, and statuses in the jobs file.
    file = open(os.path.join(RAW_FOLDER, "maintenance_jobs_export.csv"), encoding="utf-8")
    reader = csv.DictReader(file)
    job_ids = set()
    depot_counts = {}
    status_counts = {}
    for row in reader:
        job_ids.add(clean_job_id(row["job_id"]))

        depot = clean_depot(row["depot"])
        if depot not in depot_counts:
            depot_counts[depot] = 0
        depot_counts[depot] += 1

        status = clean_status(row["current_status"])
        if status not in status_counts:
            status_counts[status] = 0
        status_counts[status] += 1
    file.close()
    print("Unique job IDs:", len(job_ids))
    print("Depots:", depot_counts)
    print("Statuses:", status_counts)

    # Test 4: every delay should now match a job.
    missing = 0
    for file_name in ["delay_events_legacy.csv", "delay_events_2024.csv", "delay_events_current.csv"]:
        file = open(os.path.join(RAW_FOLDER, file_name), encoding="utf-8")
        for row in csv.DictReader(file):
            if clean_job_id(row["job_id"]) not in job_ids:
                missing += 1
        file.close()
    print("Delay rows whose job can't be found:", missing)