# cleaning.py
# Phase 3: functions that clean the raw data, one problem at a time.

import csv
import os
from datetime import datetime

PROJECT_FOLDER = os.path.dirname(os.path.abspath(__file__))
RAW_FOLDER = os.path.join(PROJECT_FOLDER, "data", "raw")
CLEAN_FOLDER = os.path.join(PROJECT_FOLDER, "data", "clean")


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

# Every raw spelling of a delay category (in capitals), and the standard name it means.
CATEGORY_MAP = {
    "DISCOVERED_WORK": "discovered_work",
    "D/W": "discovered_work",
    "DISC WORK": "discovered_work",
    "UNPLANNED": "discovered_work",
    "PARTS": "parts",
    "PART": "parts",
    "PRTS": "parts",
    "SUPPLY": "parts",
    "ENGINEERING_APPROVAL": "engineering_approval",
    "ENGINEERING": "engineering_approval",
    "ENG APPR": "engineering_approval",
    "TECH DISP": "engineering_approval",
    "STAFFING": "staffing",
    "STAFF": "staffing",
    "MANPOWER": "staffing",
    "OTHER": "other",
    "MISC": "other",
}


def clean_category(text):
    """Turn any spelling of a delay category into one of the 5 standard names, or None if unknown."""
    text = text.strip().upper()
    if text in CATEGORY_MAP:
        return CATEGORY_MAP[text]
    return None


def clean_days(text):
    """Turn days_added into a whole number, or None if it's missing or a placeholder value."""
    text = text.strip().lower()
    if text == "" or text == "null":
        return None
    text = text.replace("days", "").replace("day", "").strip()
    days = int(text)
    if days < 0 or days == 999:
        return None
    return days


def load_delay_events():
    """Read all 3 delay files and return a dictionary of unique events, keyed by event_id."""
    events = {}
    duplicates = 0
    for file_name in ["delay_events_legacy.csv", "delay_events_2024.csv", "delay_events_current.csv"]:
        file = open(os.path.join(RAW_FOLDER, file_name), encoding="utf-8")
        for row in csv.DictReader(file):
            if row["event_id"] in events:
                duplicates += 1
            else:
                events[row["event_id"]] = row
        file.close()
    print("Duplicate delay rows skipped:", duplicates)
    return events

def clean_version(text):
    """Turn a version like "v2" or "2" into the whole number 2."""
    text = text.strip().lower().replace("v", "")
    return int(text)


def load_estimates():
    """Read the estimate history and return a dictionary of unique estimates, keyed by estimate_id."""
    estimates = {}
    duplicates = 0
    file = open(os.path.join(RAW_FOLDER, "target_estimate_history.csv"), encoding="utf-8")
    for row in csv.DictReader(file):
        if row["estimate_id"] in estimates:
            duplicates += 1
        else:
            estimates[row["estimate_id"]] = row
    file.close()
    print("Duplicate estimate rows skipped:", duplicates)
    return estimates


def days_moved_by_each_delay(estimates):
    """For every revision caused by a delay, work out how many days it moved the target date.

    Returns a dictionary: event_id -> days the target moved.
    """
    # First, look up any job's target date by (job_id, version).
    targets = {}
    for estimate in estimates.values():
        key = (clean_job_id(estimate["job_id"]), clean_version(estimate["version"]))
        targets[key] = parse_date(estimate["target_completion_date"])

    # Then, for each revision a delay caused, subtract the previous version's target.
    days_moved = {}
    for estimate in estimates.values():
        event_id = estimate["trigger_event_id"].strip()
        if event_id == "":
            continue
        job_id = clean_job_id(estimate["job_id"])
        version = clean_version(estimate["version"])
        new_target = targets[(job_id, version)]
        old_target = targets[(job_id, version - 1)]
        days_moved[event_id] = (new_target - old_target).days
    return days_moved

def clean_description(text):
    """Lowercase a description and spell out the abbreviation "insp"."""
    words = text.strip().lower().split()
    for i in range(len(words)):
        if words[i] == "insp":
            words[i] = "inspection"
    return " ".join(words)


def build_clean_delays(events, days_moved):
    """Turn the raw delay rows into a list of clean delays, filling in missing days."""
    clean_delays = []
    filled_in = 0
    for event_id, event in events.items():
        days = clean_days(event["days_added"])
        if days is None:
            days = days_moved[event_id]
            filled_in += 1
        delay = {
            "event_id": event_id,
            "job_id": clean_job_id(event["job_id"]),
            "sequence": int(event["event_sequence"]),
            "logged_at": parse_date(event["logged_at"]),
            "category": clean_category(event["delay_category"]),
            "description": clean_description(event["description"]),
            "days_added": days,
        }
        clean_delays.append(delay)
    print("Missing days filled in from the estimate history:", filled_in)
    return clean_delays

# The raw estimate types, and the shorter names used from here on.
ESTIMATE_TYPES = {
    "ORIGINAL": "original",
    "REVISION": "revision",
    "POST_COMPLETION_REVISION": "post_completion",
}


def build_clean_estimates(estimates):
    """Turn the raw estimate rows into a list of clean estimates."""
    clean_estimates = []
    for estimate_id, estimate in estimates.items():
        trigger = estimate["trigger_event_id"].strip()
        if trigger == "":
            trigger = None
        clean_estimate = {
            "estimate_id": estimate_id,
            "job_id": clean_job_id(estimate["job_id"]),
            "version": clean_version(estimate["version"]),
            "estimated_at": parse_date(estimate["estimated_at"]),
            "target_date": parse_date(estimate["target_completion_date"]),
            "trigger_event_id": trigger,
            "type": ESTIMATE_TYPES[estimate["estimate_type"].strip().upper()],
        }
        clean_estimates.append(clean_estimate)
    return clean_estimates

def build_clean_jobs():
    """Read the jobs file and return a list of clean jobs, with flags for logic problems."""
    clean_jobs = []
    file = open(os.path.join(RAW_FOLDER, "maintenance_jobs_export.csv"), encoding="utf-8")
    for row in csv.DictReader(file):
        open_date = parse_date(row["open_date"])
        completion_date = parse_date(row["actual_completion_date"])
        status = clean_status(row["current_status"])
        job = {
            "job_id": clean_job_id(row["job_id"]),
            "asset": row["asset_ref"].strip(),
            "asset_type": row["asset_type"].strip(),
            "depot": clean_depot(row["depot"]),
            "open_date": open_date,
            "original_target": parse_date(row["original_target_date"]),
            "current_target": parse_date(row["current_target_date"]),
            "completion_date": completion_date,
            "status": status,
            # Logic problems: flagged, not deleted.
            "status_conflict": status == "open" and completion_date is not None,
            "same_day": completion_date == open_date,
        }
        clean_jobs.append(job)
    file.close()
    return clean_jobs

def add_day_counts(clean_jobs, clean_delays, clean_estimates):
    """Add calendar-day counts, measured from each job's open date (day 0)."""
    open_dates = {}
    for job in clean_jobs:
        open_date = job["open_date"]
        open_dates[job["job_id"]] = open_date
        job["original_target_days"] = (job["original_target"] - open_date).days
        job["current_target_days"] = (job["current_target"] - open_date).days
        job["completion_days"] = (job["completion_date"] - open_date).days
    for delay in clean_delays:
        open_date = open_dates[delay["job_id"]]
        delay["logged_day"] = (delay["logged_at"] - open_date).days
    for estimate in clean_estimates:
        open_date = open_dates[estimate["job_id"]]
        estimate["estimated_day"] = (estimate["estimated_at"] - open_date).days
        estimate["target_days"] = (estimate["target_date"] - open_date).days


def write_csv(file_name, rows):
    """Write a list of dictionaries to a CSV file in data/clean/."""
    os.makedirs(CLEAN_FOLDER, exist_ok=True)
    file = open(os.path.join(CLEAN_FOLDER, file_name), "w", encoding="utf-8", newline="")
    writer = csv.DictWriter(file, fieldnames=list(rows[0].keys()))
    writer.writeheader()
    writer.writerows(rows)
    file.close()
    print("Wrote", len(rows), "rows to", file_name)

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

    # Test 5: load the delay events, then clean their categories and days.
    events = load_delay_events()
    print("Unique delay events:", len(events))
    category_counts = {}
    missing_days = 0
    for event in events.values():
        category = clean_category(event["delay_category"])
        if category not in category_counts:
            category_counts[category] = 0
        category_counts[category] += 1
        if clean_days(event["days_added"]) is None:
            missing_days += 1
    print("Categories:", category_counts)
    print("Delays with missing or placeholder days:", missing_days)

    # Test 6: check that days_added always equals how far the target moved,
    # then use that to fill in the missing ones.
    estimates = load_estimates()
    print("Unique estimates:", len(estimates))
    days_moved = days_moved_by_each_delay(estimates)
    matches = 0
    mismatches = 0
    recovered = 0
    for event_id, event in events.items():
        days = clean_days(event["days_added"])
        if days is None:
            if event_id in days_moved:
                recovered += 1
        elif days == days_moved[event_id]:
            matches += 1
        else:
            mismatches += 1
    print("Valid days that match the estimate history:", matches)
    print("Valid days that don't match:", mismatches)
    print("Missing days that can be recovered:", recovered)

    # Test 7: build the clean delay list and check it.
    clean_delays = build_clean_delays(events, days_moved)
    print("Clean delays:", len(clean_delays))
    descriptions = set()
    total_days = 0
    for delay in clean_delays:
        descriptions.add(delay["description"])
        total_days += delay["days_added"]
    print("Different descriptions:", len(descriptions))
    print("Total delay days:", total_days)
    print("First clean delay:", clean_delays[0])

    # Test 8: build the clean estimate list and check each job's versions.
    clean_estimates = build_clean_estimates(estimates)
    print("Clean estimates:", len(clean_estimates))
    type_counts = {}
    versions_by_job = {}
    for estimate in clean_estimates:
        if estimate["type"] not in type_counts:
            type_counts[estimate["type"]] = 0
        type_counts[estimate["type"]] += 1
        if estimate["job_id"] not in versions_by_job:
            versions_by_job[estimate["job_id"]] = []
        versions_by_job[estimate["job_id"]].append(estimate["version"])
    print("Estimate types:", type_counts)
    jobs_with_gaps = 0
    for job_id, versions in versions_by_job.items():
        versions.sort()
        if versions != list(range(1, len(versions) + 1)):
            jobs_with_gaps += 1
    print("Jobs with estimates:", len(versions_by_job))
    print("Jobs with missing or repeated versions:", jobs_with_gaps)

    # Test 9: build the clean jobs, count the logic problems,
    # and cross-check the jobs against the estimate history.
    clean_jobs = build_clean_jobs()
    print("Clean jobs:", len(clean_jobs))
    conflicts = 0
    same_day = 0
    original_by_job = {}
    completion_by_job = {}
    for job in clean_jobs:
        if job["status_conflict"]:
            conflicts += 1
        if job["same_day"]:
            same_day += 1
        original_by_job[job["job_id"]] = job["original_target"]
        completion_by_job[job["job_id"]] = job["completion_date"]
    print("Jobs marked open that have a completion date:", conflicts)
    print("Jobs finished the same day they opened:", same_day)
    original_mismatches = 0
    post_completion_at_finish = 0
    for estimate in clean_estimates:
        job_id = estimate["job_id"]
        if estimate["type"] == "original" and estimate["target_date"] != original_by_job[job_id]:
            original_mismatches += 1
        if estimate["type"] == "post_completion" and estimate["target_date"] == completion_by_job[job_id]:
            post_completion_at_finish += 1
    print("Original targets that don't match the estimate history:", original_mismatches)
    print("Post-completion revisions set to the exact finish date:", post_completion_at_finish)

    # Test 10: add day counts, check one job by hand, then save everything.
    add_day_counts(clean_jobs, clean_delays, clean_estimates)
    for job in clean_jobs:
        if job["job_id"] == "JOB-0000058":
            print("JOB-0000058 opened:", job["open_date"])
            print("  Original target:", job["original_target"], "=", job["original_target_days"], "days")
            print("  Finished:", job["completion_date"], "=", job["completion_days"], "days")
            print("  Days late vs original:", job["completion_days"] - job["original_target_days"])
    write_csv("jobs.csv", clean_jobs)
    write_csv("delays.csv", clean_delays)
    write_csv("estimates.csv", clean_estimates)