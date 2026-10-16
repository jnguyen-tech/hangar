# app.py
# Phase 7: the web version of the maintenance delay tracker.
# Run it with:  python app.py
# Then open http://127.0.0.1:5000 in your browser.

from flask import Flask, render_template
from load_data import load_tracker
from charts import count_on_time
from maintenance_tracker import percent
from demo_data import load_demo_tracker

app = Flask(__name__)

# True = made-up sample jobs, safe to show anyone.
# False = the real dataset in data/clean/ (keep it private).
DEMO = True

# Load all the jobs once, when the program starts.
print("Loading jobs...")
if DEMO:
    tracker = load_demo_tracker()
else:
    tracker = load_tracker()
print("Loaded", len(tracker.jobs), "jobs")


@app.context_processor
def add_demo_flag():
    """Let every page know whether this is the demo, so it can show the banner."""
    return {"demo": DEMO}


@app.route("/")
def home():
    """The home page."""
    return render_template("index.html")


@app.route("/jobs")
def job_list():
    """A table of the first 100 jobs."""
    rows = []
    for job in tracker.jobs[:100]:
        original = tracker.get_original_estimate(job.job_id).target_days
        row = {
            "job_id": job.job_id,
            "asset": job.asset,
            "status": job.status,
            "original_days": original,
            "actual_days": job.actual_days,
            "days_late": job.actual_days - original,
        }
        rows.append(row)
    return render_template("jobs.html", rows=rows, total=len(tracker.jobs))


@app.route("/jobs/<job_id>")
def job_page(job_id):
    """One job: its targets, its full estimate history, and its delays."""
    job = tracker.find_job(job_id)
    if job is None:
        return "Job not found", 404

    original = tracker.get_original_estimate(job_id).target_days
    last_regular = tracker.get_last_regular_estimate(job_id).target_days
    final = tracker.get_current_estimate(job_id).target_days

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
        job=job,
        original=original,
        last_regular=last_regular,
        final=final,
        days_late=job.actual_days - original,
        history=history,
        delays=delays,
    )


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


if __name__ == "__main__":
    app.run(debug=True)
