# load_data.py
# Phase 3: load the clean data into the Tracker and run the reports.
# Run cleaning.py first, so the files in data/clean/ exist.

import csv
import os
from maintenance_tracker import Tracker

PROJECT_FOLDER = os.path.dirname(os.path.abspath(__file__))
CLEAN_FOLDER = os.path.join(PROJECT_FOLDER, "data", "clean")

CATEGORIES = ["discovered_work", "parts", "engineering_approval", "staffing", "other"]


def read_csv(file_name):
    """Read one file from data/clean/ and return its rows as a list of dictionaries."""
    file = open(os.path.join(CLEAN_FOLDER, file_name), encoding="utf-8")
    rows = list(csv.DictReader(file))
    file.close()
    return rows


def load_tracker():
    """Build a Tracker from the clean files: create each job, replay its delays in order, then close it."""
    jobs = read_csv("jobs.csv")
    delays = read_csv("delays.csv")

    # Look up any delay by (job_id, sequence), so each job's delays can be replayed in order.
    delay_lookup = {}
    for delay in delays:
        delay_lookup[(delay["job_id"], int(delay["sequence"]))] = delay

    tracker = Tracker()
    tracker.quiet = True
    tracker.set_categories(CATEGORIES)

    for job in jobs:
        job_id = job["job_id"]
        tracker.create_job(job_id, job["asset"], int(job["original_target_days"]))

        sequence = 1
        while (job_id, sequence) in delay_lookup:
            delay = delay_lookup[(job_id, sequence)]
            tracker.log_delay(
                job_id,
                int(delay["logged_day"]),
                delay["category"],
                delay["description"],
                int(delay["days_added"]),
                delay["event_id"],
            )
            sequence += 1

        tracker.close_job(job_id, int(job["completion_days"]))

    return tracker


def check_against_dataset(tracker):
    """Check that the Tracker rebuilt the same estimate history the dataset recorded."""
    dataset_targets = {}
    for estimate in read_csv("estimates.csv"):
        if estimate["type"] != "post_completion":
            key = (estimate["job_id"], int(estimate["version"]))
            dataset_targets[key] = int(estimate["target_days"])

    matches = 0
    mismatches = 0
    for estimate in tracker.estimates:
        if dataset_targets[(estimate.job_id, estimate.version)] == estimate.target_days:
            matches += 1
        else:
            mismatches += 1
    print("Rebuilt estimates that match the dataset:", matches)
    print("Rebuilt estimates that don't match:", mismatches)


if __name__ == "__main__":
    tracker = load_tracker()
    print("Jobs loaded:", len(tracker.jobs))
    print("Delays logged:", len(tracker.delay_events))
    print("Estimates created:", len(tracker.estimates))
    check_against_dataset(tracker)
    tracker.print_job_report("JOB-0000058")
    tracker.print_summary_report()