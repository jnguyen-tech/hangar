# prototype.py
#
# Phase 1 of the Maintenance Delay Tracker: a plain-Python version.
# There's no database yet. Each "table" is a list of dictionaries in memory.
#
# The one idea behind the whole file:
#   A job's planned finish is never overwritten. Every delay ADDS a new
#   estimate, so the original plan and every change stay on record.
#
# This file is the general tool. Nothing in it is specific to aircraft or to
# Tinker AFB -- an "asset" can be an aircraft, a truck, a building, or a
# laptop. Scenarios (like tinker_case_study.py) import this file, choose their
# own delay categories, and feed in their own jobs.
#
# Days are plain numbers ("day 0" = the day the job opened) to keep the math
# simple. The database version (schema.sql) will use real dates.
#
# Companion sheet: PROTOTYPE_GUIDE.md explains every part of this file.
#
# Sections:
#   1. Data (the three lists and the delay categories)
#   2. Small helpers
#   3. Jobs
#   4. Estimates
#   5. Delay events
#   6. Reports


# ===========================================================================
# 1. Data
# ===========================================================================

jobs = []          # one dictionary per maintenance job
estimates = []     # one dictionary per VERSION of a job's planned finish
delay_events = []  # one dictionary per problem that pushed a finish out

# The allowed reasons for a delay. A fixed list is what makes the
# "slip by cause" totals possible. These are the defaults; a scenario can
# replace them with set_categories() before logging any delays.
categories = ["discovered_work", "parts", "staffing", "other"]


def set_categories(new_categories):
    """Replace the allowed delay categories. Call this before logging any delays."""
    categories.clear()
    for category in new_categories:
        categories.append(category)


# ===========================================================================
# 2. Small helpers
# ===========================================================================

def rows_for_job(table, job_id):
    """Return every row in a table (a list of dictionaries) that belongs to job_id."""
    matches = []
    for row in table:
        if row["job_id"] == job_id:
            matches.append(row)
    return matches


def total_days_by_category(events):
    """Add up days_added for each category.

    Returns a dictionary like {"discovered_work": 35, "parts": 10, ...}.
    """
    totals = {}
    for category in categories:
        totals[category] = 0

    for event in events:
        totals[event["category"]] += event["days_added"]

    return totals


def percent(part, whole):
    """Return part as a percentage of whole, rounded to 1 decimal place."""
    if whole == 0:
        return 0.0
    return round(part / whole * 100, 1)


# ===========================================================================
# 3. Jobs
# ===========================================================================

def find_job(job_id):
    """Return the job with this id, or None if there isn't one."""
    for job in jobs:
        if job["job_id"] == job_id:
            return job
    return None


def create_job(job_id, asset, planned_days):
    """Open a new job on an asset and record its ORIGINAL estimate as version 1."""
    if find_job(job_id) is not None:
        print(f"Error: job {job_id} already exists")
        return

    jobs.append({
        "job_id": job_id,
        "asset": asset,
        "status": "open",
        "actual_days": None,  # filled in when the job closes
    })

    # Version 1 is the original plan. It is never changed or deleted.
    # (In the Tinker case study, this is the number GAO Recommendation 1
    # says should be reported.)
    estimates.append({
        "job_id": job_id,
        "version": 1,
        "target_days": planned_days,
        "created_on_day": 0,
        "reason": "original plan",
        "delay_event_id": None,
    })

    print(f"Created job {job_id} for {asset}, planned for {planned_days} days")


def close_job(job_id, actual_days):
    """Mark a job finished and record how many days it actually took."""
    job = find_job(job_id)
    if job is None:
        print(f"Error: job {job_id} not found")
        return

    job["status"] = "closed"
    job["actual_days"] = actual_days
    print(f"Closed job {job_id} after {actual_days} days")


# ===========================================================================
# 4. Estimates  (append-only: add new versions, never change old ones)
# ===========================================================================

def get_estimates_for_job(job_id):
    """Every estimate for a job, oldest first."""
    return rows_for_job(estimates, job_id)


def get_original_estimate(job_id):
    """The first estimate ever made for a job."""
    return get_estimates_for_job(job_id)[0]


def get_current_estimate(job_id):
    """The most recent estimate for a job."""
    return get_estimates_for_job(job_id)[-1]


def revise_estimate(job_id, delay_event):
    """Add a NEW estimate version for a delay. Older versions are left alone."""
    current = get_current_estimate(job_id)

    estimates.append({
        "job_id": job_id,
        "version": current["version"] + 1,
        "target_days": current["target_days"] + delay_event["days_added"],
        "created_on_day": delay_event["logged_on_day"],
        "reason": delay_event["description"],
        "delay_event_id": delay_event["event_id"],
    })


# ===========================================================================
# 5. Delay events
# ===========================================================================

def get_delays_for_job(job_id):
    """Every delay event for a job, oldest first."""
    return rows_for_job(delay_events, job_id)


def log_delay(job_id, logged_on_day, category, description, days_added):
    """Record a delay, then automatically add a revised estimate."""
    if find_job(job_id) is None:
        print(f"Error: job {job_id} not found")
        return

    if category not in categories:
        print(f"Error: '{category}' is not a valid category. Use one of: {categories}")
        return

    event = {
        "event_id": len(delay_events) + 1,
        "job_id": job_id,
        "category": category,
        "description": description,
        "logged_on_day": logged_on_day,
        "days_added": days_added,
    }
    delay_events.append(event)
    revise_estimate(job_id, event)

    print(f"Job {job_id}, day {logged_on_day}: {category} (+{days_added} days) - {description}")


# ===========================================================================
# 6. Reports
# ===========================================================================

def print_job_report(job_id):
    """One job: original vs. current target, full history, and slip by cause."""
    job = find_job(job_id)
    if job is None:
        print(f"Error: job {job_id} not found")
        return

    original = get_original_estimate(job_id)["target_days"]
    current = get_current_estimate(job_id)["target_days"]
    slip = current - original

    print(f"\n=== Job {job_id}: {job['asset']} ({job['status']}) ===")
    print(f"Original target: {original} days")
    print(f"Current target:  {current} days")
    print(f"Slip:            {slip} days ({percent(slip, original)}% over the original plan)")

    print("Estimate history:")
    for estimate in get_estimates_for_job(job_id):
        print(f"  v{estimate['version']}: {estimate['target_days']} days - {estimate['reason']}")

    print("Slip by cause:")
    delays = get_delays_for_job(job_id)
    if len(delays) == 0:
        print("  none - no delays logged")
    else:
        totals = total_days_by_category(delays)
        for category in categories:
            if totals[category] > 0:
                print(f"  {category}: {totals[category]} days")

    if job["status"] == "closed":
        print(f"Actually finished in {job['actual_days']} days")


def print_slip_by_cause():
    """Across all jobs: total days of slip, split by cause."""
    totals = total_days_by_category(delay_events)

    total_slip = 0
    for category in categories:
        total_slip += totals[category]

    print(f"Total slip across all jobs: {total_slip} days")
    for category in categories:
        days = totals[category]
        print(f"  {category}: {days} days ({percent(days, total_slip)}%)")


def print_on_time_comparison():
    """'On time' looks different against original targets vs. revised ones."""
    closed_jobs = []
    for job in jobs:
        if job["status"] == "closed":
            closed_jobs.append(job)

    on_time_vs_original = 0
    on_time_vs_revised = 0
    for job in closed_jobs:
        original = get_original_estimate(job["job_id"])["target_days"]
        revised = get_current_estimate(job["job_id"])["target_days"]
        if job["actual_days"] <= original:
            on_time_vs_original += 1
        if job["actual_days"] <= revised:
            on_time_vs_revised += 1

    hidden = on_time_vs_revised - on_time_vs_original

    print(f"\nClosed jobs: {len(closed_jobs)}")
    print(f"  On time measured against REVISED targets:  {on_time_vs_revised} of {len(closed_jobs)}")
    print(f"  On time measured against ORIGINAL targets: {on_time_vs_original} of {len(closed_jobs)}")
    print(f"  Jobs that only look on time because the target moved: {hidden}")


def print_summary_report():
    """Roll up every job."""
    print("\n=========== SUMMARY: ALL JOBS ===========")
    print_slip_by_cause()
    print_on_time_comparison()


# This file is the tool itself. To see it in action, run a scenario file.
if __name__ == "__main__":
    print("prototype.py is the general tool. Run a scenario to see it work:")
    print("  python3 tinker_case_study.py")
