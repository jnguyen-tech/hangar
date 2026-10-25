# app.py
# Phase 7: the web version of the maintenance delay tracker.
# Run it with:  python app.py
# Then open http://127.0.0.1:5000 in your browser.

import os
import time
from flask import Flask, render_template, request, redirect, url_for, abort, session
from load_data import load_tracker, CLEAN_FOLDER
from charts import count_on_time
from maintenance_tracker import percent
from demo_data import load_demo_tracker
from accounts import USERS_FILE, load_accounts, can
import database

app = Flask(__name__)

# Flask remembers who is logged in with a "session" cookie in the browser.
# The secret key signs that cookie so nobody can fake it. It must never be
# on GitHub, so it comes from the server's settings (on PythonAnywhere, the
# WSGI file). If it isn't set, a random one is made, which works but logs
# everyone out whenever the site restarts.
app.secret_key = os.environ.get("HANGAR_SECRET_KEY", os.urandom(32))

# "Lax" stops other websites from sending forms here using your login.
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

# How many jobs to show on one page of the Jobs table.
JOBS_PER_PAGE = 100

# Login lockout: after 5 wrong passwords in a row, that account has to wait
# 10 minutes before it can try again. This stops someone from guessing
# password after password.
MAX_LOGIN_TRIES = 5
LOCKOUT_MINUTES = 10
failed_logins = {}   # username -> {"count": wrong tries in a row, "locked_until": a time}

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

# Changes made on the website are saved in a SQLite database (see database.py).
# Demo mode gets its own file, so made-up jobs never mix with the real ones.
if DEMO:
    DB_FILE = database.DEMO_DB
else:
    DB_FILE = database.MAIN_DB
database.create_tables(DB_FILE)
replayed = database.replay_history(DB_FILE, tracker)
print("Replayed", replayed, "saved changes from", os.path.basename(DB_FILE))

# The website's logins, from users.csv (made by add_user.py).
accounts = load_accounts(USERS_FILE)
print("Loaded", len(accounts.users), "accounts")


def current_user():
    """Return the logged-in User, or None if nobody is logged in."""
    # session works like a dictionary that lasts between pages for one browser.
    username = session.get("username")
    if username is None:
        return None
    user = accounts.find_user(username)
    if user is None or not user.active:
        return None
    return user


@app.context_processor
def add_page_flags():
    """Give every page: the demo flag, who is logged in, and what they're allowed to do."""
    user = current_user()
    return {
        "demo": DEMO,
        "user": user,
        "can_open_job": can(user, "open_job"),
        "can_log_delay": can(user, "log_delay"),
        "can_close_job": can(user, "close_job"),
    }


def whole_number(text):
    """Turn form text like "12" into the number 12.

    Everything typed into a form arrives as text. If the text isn't a
    whole number (like "abc", "-3", or "2.5"), return None instead.
    """
    text = text.strip()
    # isdecimal() is True only for plain digits like "120".
    # (isdigit() also says True for things like "²", which int() can't read.)
    if text.isdecimal():
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
    page = whole_number(page)
    if page is None or page < 1:
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
            "logged_by": event.logged_by,
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
# Forms that change the data. Each one checks the logged-in user's role first.
# The tracker checks the details. If it accepts the change, it's also saved
# to the database, so it's still there after the site restarts.
# ---------------------------------------------------------------------------

@app.route("/jobs/new", methods=["GET", "POST"])
def new_job():
    """GET shows the empty form. POST is what happens when you press "Open job"."""
    # Hiding the form isn't enough: someone could still send data to this
    # address. So the route itself checks (403 means "not allowed").
    user = current_user()
    if not can(user, "open_job"):
        abort(403)

    error = None
    if request.method == "POST":
        # request.form holds what was typed, by each input's name="...".
        job_id = request.form["job_id"].strip().upper()
        asset = request.form["asset"].strip()
        planned_days = whole_number(request.form["planned_days"])

        if job_id == "" or asset == "":
            error = "Please fill in the job ID and the asset."
        elif len(job_id) > 20 or len(asset) > 30:
            error = "Job IDs can be up to 20 characters, and assets up to 30."
        elif not job_id.replace("-", "").isalnum():
            error = "Job IDs can only use letters, numbers, and dashes, like NEW-0001."
        elif planned_days is None:
            error = "Planned days must be a whole number, like 120."
        else:
            # create_job returns an error message, or None if it worked.
            error = tracker.create_job(job_id, asset, planned_days)

        if error is None:
            database.save_opened_job(DB_FILE, job_id, asset, planned_days, user.username)
            # It worked, so send the browser to the new job's page.
            return redirect(url_for("job_page", job_id=job_id))

    return render_template("new_job.html", error=error, form=request.form)


@app.route("/jobs/<job_id>/delay", methods=["POST"])
def add_delay(job_id):
    """Log a delay on an open job. This adds a new estimate version too."""
    user = current_user()
    if not can(user, "log_delay"):
        abort(403)

    day = whole_number(request.form["day"])
    days_added = whole_number(request.form["days_added"])
    category = request.form["category"]
    description = request.form["description"].strip()

    if day is None or days_added is None:
        error = "Day logged and days added must be whole numbers."
    elif description == "":
        error = "Please describe what caused the delay."
    elif len(description) > 200:
        error = "Please keep the description under 200 characters."
    else:
        # logged_by stamps the delay with who entered it.
        error = tracker.log_delay(job_id, day, category, description, days_added,
                                  logged_by=user.username)
        if error is None:
            database.save_delay(DB_FILE, job_id, day, category, description, days_added, user.username)

    # Go back to the job's page either way. If something went wrong,
    # put the message in the address so the page can show it.
    if error is None:
        return redirect(url_for("job_page", job_id=job_id))
    return redirect(url_for("job_page", job_id=job_id, error=error))


@app.route("/jobs/<job_id>/close", methods=["POST"])
def close_job(job_id):
    """Close an open job and record how many days it really took."""
    user = current_user()
    if not can(user, "close_job"):
        abort(403)

    actual_days = whole_number(request.form["actual_days"])
    if actual_days is None:
        error = "Finished in must be a whole number of days."
    else:
        error = tracker.close_job(job_id, actual_days)
        if error is None:
            database.save_closed_job(DB_FILE, job_id, actual_days, user.username)

    if error is None:
        return redirect(url_for("job_page", job_id=job_id))
    return redirect(url_for("job_page", job_id=job_id, error=error))


# ---------------------------------------------------------------------------
# Logging in and out
# ---------------------------------------------------------------------------

@app.route("/login", methods=["GET", "POST"])
def login():
    """GET shows the login form. POST checks the username and password."""
    error = None
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]

        # time.time() is the current time in seconds. If this account's
        # locked_until time is still in the future, it's locked.
        record = failed_logins.get(username)
        if record is not None and record["locked_until"] > time.time():
            error = f"Too many wrong tries. Please wait {LOCKOUT_MINUTES} minutes and try again."
            return render_template("login.html", error=error)

        user = accounts.login(username, password)
        if user is None:
            # Same message either way, so nobody can learn which usernames exist.
            error = "Wrong username or password."
            # Only count tries for real accounts, so the dictionary stays small.
            if accounts.find_user(username) is not None:
                if record is None:
                    record = {"count": 0, "locked_until": 0}
                record["count"] = record["count"] + 1
                if record["count"] >= MAX_LOGIN_TRIES:
                    record["locked_until"] = time.time() + LOCKOUT_MINUTES * 60
                    record["count"] = 0
                failed_logins[username] = record
        else:
            # Logged in, so forget any earlier wrong tries.
            if username in failed_logins:
                del failed_logins[username]
            session.clear()
            session["username"] = user.username
            return redirect(url_for("home"))
    return render_template("login.html", error=error)


@app.route("/logout")
def logout():
    """Forget who was logged in, then go back to the home page."""
    session.clear()
    return redirect(url_for("home"))


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
    app.run(debug=True)
