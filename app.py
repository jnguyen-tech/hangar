# app.py
# Phase 7: the web version of the maintenance delay tracker.
# Run it with:  python app.py
# Then open http://127.0.0.1:5000 in your browser.

from flask import Flask, render_template
from load_data import load_tracker

app = Flask(__name__)

# Load all the jobs once, when the program starts.
print("Loading jobs...")
tracker = load_tracker()
print("Loaded", len(tracker.jobs), "jobs")


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

if __name__ == "__main__":
    app.run(debug=True)