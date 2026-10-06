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


if __name__ == "__main__":
    app.run(debug=True)