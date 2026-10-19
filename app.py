# app.py
# Phase 7: the web version of the maintenance delay tracker.
# Run it with:  python app.py
# Then open http://127.0.0.1:5000 in your browser.

import os
from flask import Flask, render_template, request, redirect, url_for, abort
from load_data import load_tracker, CLEAN_FOLDER
from charts import count_on_time
from maintenance_tracker import percent
from demo_data import load_demo_tracker

app = Flask(__name__)

# How many jobs to show on one page of the Jobs table.
JOBS_PER_PAGE = 100

# Can people add jobs, log delays, and close jobs from the website?
# It starts False, so the public website is read-only.
# The last lines of this file switch it to True, but only when YOU run
# "python app.py" on your own computer. (A web host skips those lines.)
ALLOW_EDITS = False

# Use the 50,000-job dataset if its clean files are here.
# If they aren't (for example, someone downloaded the code from GitHub,
# where the data isn't included), use 200 made-up demo jobs instead.
if os.path.exists(os.path.join(CLEAN_FOLDER, "jobs.csv")):
    DEMO = False
else:
    DEMO = True

# Load all the jobs once, when the program starts.
print("Loading jobs...")
if DEMO:
    tracker = load_demo_tracker()
else:
    tracker = load_tracker()
print("Loaded", len(tracker.jobs), "jobs")


@app.context_processor
def add_page_flags():
    """Let every page know if this is the demo (for the banner) and if editing is on (for the forms)."""
    return {"demo": DEMO, "allow_edits": ALLOW_EDITS}


def whole_number(text):
    """Turn form text like "12" into the number 12.

    Everything typed into a form arrives as text. If the text isn't a
    whole number (like "abc", "-3", or "2.5"), return None instead.
    """
    text = text.strip()
    if text.isdigit():
        return int(text)
    return None


@app.route("/")
def home():
    """The home page."""
    return render_template("index.html", total=len(tracker.jobs))


@app.route("/jobs")
def job_list():
    """A table of jobs, 100 per page. The search box looks through EVERY job."""
    # request.args holds whatever comes after the ? in the web address.
    # For /jobs?search=b-52&page=2, search is "b-52" and page is "2".
    # The "" and "1" are what to use when nothing was given.
    search = request.args.get("search", "").strip()
    page = request.args.get("page", "1")

    # The page number arrives as text, so turn it into a whole number.
    # If someone types something odd like page=abc, just use page 1.
    if page.isdigit() and int(page) >= 1:
        page = int(page)
    else:
        page = 1

    # Step 1: find every job that matches the search.
    # An empty search ("") is "in" every piece of text, so it matches all jobs.
    matches = []
    for job in tracker.jobs:
        job_text = (str(job.job_id) + " " + str(job.asset) + " " + job.status).lower()
        if search.lower() in job_text:
            matches.append(job)

    # Step 2: work out how many pages that is (rounding up).
    total_pages = len(matches) // JOBS_PER_PAGE
    if len(matches) % JOBS_PER_PAGE != 0:
        total_pages = total_pages + 1
    if total_pages == 0:
        total_pages = 1
    if page > total_pages:
        page = total_pages

    # Step 3: cut out just the jobs for this page.
    # Page 1 is matches[0:100], page 2 is matches[100:200], and so on.
    start = (page - 1) * JOBS_PER_PAGE
    end = start + JOBS_PER_PAGE

    rows = []
    for job in matches[start:end]:
        original = tracker.get_original_estimate(job.job_id).target_days
        if job.actual_days is None:
            days_late = "still open"
        else:
            days_late = job.actual_days - original
        row = {
            "job_id": job.job_id,
            "asset": job.asset,
            "status": job.status,
            "original_days": original,
            "actual_days": job.actual_days,
            "days_late": days_late,
        }
        rows.append(row)

    return render_template(
        "jobs.html",
        rows=rows,
        total=len(tracker.jobs),
        search=search,
        match_count=len(matches),
        page=page,
        total_pages=total_pages,
        first_number=start + 1,
        last_number=start + len(rows),
    )


@app.route("/jobs/<job_id>")
def job_page(job_id):
    """One job: its targets, its full estimate history, and its delays."""
    job = tracker.find_job(job_id)
    if job is None:
        return "Job not found", 404

    original = tracker.get_original_estimate(job_id).target_days
    last_regular = tracker.get_last_regular_estimate(job_id).target_days
    final = tracker.get_current_estimate(job_id).target_days
    if job.actual_days is None:
        days_late = "still open"
    else:
        days_late = job.actual_days - original

    history = []
    for estimate in tracker.get_estimates_for_job(job_id):
        if estimate.version == 1:
            when = "At the start"
        elif estimate.after_completion:
            when = "After the job finished"
        else:
            when = "During the job"
        history.append({
            "version": estimate.version,
            "target_days": estimate.target_days,
            "reason": estimate.reason,
            "when": when,
        })

    delays = []
    for event in tracker.get_delays_for_job(job_id):
        delays.append({
            "day": event.logged_on_day,
            "category": event.category,
            "days_added": event.days_added,
            "description": event.description,
        })

    return render_template(
        "job.html",
        error=request.args.get("error"),
        categories=tracker.categories,
        job=job,
        original=original,
        last_regular=last_regular,
        final=final,
        days_late=days_late,
        history=history,
        delays=delays,
    )


# ---------------------------------------------------------------------------
# Forms that change the data. Each one only works when ALLOW_EDITS is True.
# Changes live in memory, so they're gone when the site restarts.
# (Saving them for good is the database step, later.)
# ---------------------------------------------------------------------------

@app.route("/jobs/new", methods=["GET", "POST"])
def new_job():
    """GET shows the empty form. POST is what happens when you press "Open job"."""
    # Hiding the form isn't enough: someone could still send data to this
    # address. So the route itself refuses (403 means "not allowed").
    if not ALLOW_EDITS:
        abort(403)

    error = None
    if request.method == "POST":
        # request.form holds what was typed, by each input's name="...".
        job_id = request.form["job_id"].strip().upper()
        asset = request.form["asset"].strip()
        planned_days = whole_number(request.form["planned_days"])

        if job_id == "" or asset == "":
            error = "Please fill in the job ID and the asset."
        elif not job_id.replace("-", "").isalnum():
            error = "Job IDs can only use letters, numbers, and dashes, like NEW-0001."
        elif planned_days is None:
            error = "Planned days must be a whole number, like 120."
        else:
            # create_job returns an error message, or None if it worked.
            error = tracker.create_job(job_id, asset, planned_days)

        if error is None:
            # It worked, so send the browser to the new job's page.
            return redirect(url_for("job_page", job_id=job_id))

    return render_template("new_job.html", error=error, form=request.form)


@app.route("/jobs/<job_id>/delay", methods=["POST"])
def add_delay(job_id):
    """Log a delay on an open job. This adds a new estimate version too."""
    if not ALLOW_EDITS:
        abort(403)

    day = whole_number(request.form["day"])
    days_added = whole_number(request.form["days_added"])
    category = request.form["category"]
    description = request.form["description"].strip()

    if day is None or days_added is None:
        error = "Day logged and days added must be whole numbers."
    elif description == "":
        error = "Please describe what caused the delay."
    else:
        error = tracker.log_delay(job_id, day, category, description, days_added)

    # Go back to the job's page either way. If something went wrong,
    # put the message in the address so the page can show it.
    if error is None:
        return redirect(url_for("job_page", job_id=job_id))
    return redirect(url_for("job_page", job_id=job_id, error=error))


@app.route("/jobs/<job_id>/close", methods=["POST"])
def close_job(job_id):
    """Close an open job and record how many days it really took."""
    if not ALLOW_EDITS:
        abort(403)

    actual_days = whole_number(request.form["actual_days"])
    if actual_days is None:
        error = "Finished in must be a whole number of days."
    else:
        error = tracker.close_job(job_id, actual_days)

    if error is None:
        return redirect(url_for("job_page", job_id=job_id))
    return redirect(url_for("job_page", job_id=job_id, error=error))


@app.route("/reports")
def reports():
    """The on-time comparison and the slip by cause, for all jobs."""
    counts = count_on_time(tracker)
    closed = counts["closed"]
    on_time_rows = [
        {"label": "Original target", "jobs": counts["original"], "percent": percent(counts["original"], closed)},
        {"label": "Last target set before the job finished", "jobs": counts["regular"], "percent": percent(counts["regular"], closed)},
        {"label": "Final record (after-the-fact revisions)", "jobs": counts["final"], "percent": percent(counts["final"], closed)},
    ]

    totals = tracker.total_days_by_category(tracker.delay_events)
    total_days = 0
    for category in tracker.categories:
        total_days += totals[category]

    cause_rows = []
    for category in tracker.categories:
        cause_rows.append({
            "category": category,
            "days": totals[category],
            "percent": percent(totals[category], total_days),
        })

    return render_template(
        "reports.html",
        closed=closed,
        on_time_rows=on_time_rows,
        total_days=total_days,
        cause_rows=cause_rows,
    )


# This part only runs when you type "python app.py" on your own computer.
# debug=True shows error details and reloads when you save a file, which is
# handy while building. A web host like PythonAnywhere starts the site its own
# way and skips this part, so debug mode is never on for the public site.
if __name__ == "__main__":
    ALLOW_EDITS = True    # editing forms are on, on your computer only
    app.run(debug=True)
