# database.py
# Saves every change made on the website (jobs opened, delays logged, jobs closed)
# in a SQLite database, so nothing is lost when the site restarts.
#
# SQLite is a whole database in one file. It comes with Python, so there's
# nothing to install. "import sqlite3" is all it takes.
#
# How it fits together:
#   1. The website starts and loads the 50,000 jobs from data/clean/ (or the demo jobs).
#   2. replay_history() reads every saved change from the database, oldest first,
#      and does it again on the tracker, so the tracker is back where it was.
#   3. Each time someone opens a job, logs a delay, or closes a job, the website
#      calls one of the save_ functions below to add a new row.
#
# The database is APPEND-ONLY: rows can be added, but never changed or deleted.
# That's enforced by the database itself (see the triggers below), so even
# someone with direct access to the file can't quietly rewrite the history.

import os
import sqlite3
from datetime import datetime

PROJECT_FOLDER = os.path.dirname(os.path.abspath(__file__))
MAIN_DB = os.path.join(PROJECT_FOLDER, "hangar.db")       # changes made on the real dataset
DEMO_DB = os.path.join(PROJECT_FOLDER, "hangar_demo.db")  # changes made in demo mode


# SQL is the language databases understand. Each CREATE TABLE makes one table,
# like a spreadsheet tab with fixed columns. "IF NOT EXISTS" means it's safe
# to run every time the site starts.
TABLES = """
CREATE TABLE IF NOT EXISTS jobs_opened (
    job_id        TEXT PRIMARY KEY,
    asset         TEXT NOT NULL,
    planned_days  INTEGER NOT NULL,
    opened_by     TEXT NOT NULL,
    opened_at     TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS delays_logged (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id         TEXT NOT NULL,
    logged_on_day  INTEGER NOT NULL,
    category       TEXT NOT NULL,
    description    TEXT NOT NULL,
    days_added     INTEGER NOT NULL,
    logged_by      TEXT NOT NULL,
    logged_at      TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS jobs_closed (
    job_id       TEXT PRIMARY KEY,
    actual_days  INTEGER NOT NULL,
    closed_by    TEXT NOT NULL,
    closed_at    TEXT NOT NULL
);
"""

# A trigger is a rule the database runs by itself. These run BEFORE any
# UPDATE or DELETE on the three tables and cancel it with an error.
# This is the "database that blocks edits and deletes to history."
TRIGGERS = ""
for table in ["jobs_opened", "delays_logged", "jobs_closed"]:
    for action in ["UPDATE", "DELETE"]:
        TRIGGERS += f"""
CREATE TRIGGER IF NOT EXISTS no_{action.lower()}_{table}
BEFORE {action} ON {table}
BEGIN
    SELECT RAISE(ABORT, 'History is append-only: rows in {table} can''t be changed or deleted');
END;
"""


def now():
    """The current date and time as text, like 2026-10-20T14:05:31."""
    return datetime.now().isoformat(timespec="seconds")


def create_tables(db_file):
    """Make the database file, its tables, and its triggers if they don't exist yet."""
    connection = sqlite3.connect(db_file)
    connection.executescript(TABLES + TRIGGERS)
    connection.commit()
    connection.close()


# --- Saving changes ----------------------------------------------------------
# Each ? is a placeholder. sqlite3 fills them in safely from the list that
# follows, so whatever someone types into a form can't break the SQL.
# (Building SQL by gluing text together is how "SQL injection" attacks happen.)

def save_opened_job(db_file, job_id, asset, planned_days, username):
    connection = sqlite3.connect(db_file)
    connection.execute(
        "INSERT INTO jobs_opened (job_id, asset, planned_days, opened_by, opened_at) VALUES (?, ?, ?, ?, ?)",
        [job_id, asset, planned_days, username, now()],
    )
    connection.commit()   # commit = actually save it to the file
    connection.close()


def save_delay(db_file, job_id, logged_on_day, category, description, days_added, username):
    connection = sqlite3.connect(db_file)
    connection.execute(
        "INSERT INTO delays_logged (job_id, logged_on_day, category, description, days_added, logged_by, logged_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        [job_id, logged_on_day, category, description, days_added, username, now()],
    )
    connection.commit()
    connection.close()


def save_closed_job(db_file, job_id, actual_days, username):
    connection = sqlite3.connect(db_file)
    connection.execute(
        "INSERT INTO jobs_closed (job_id, actual_days, closed_by, closed_at) VALUES (?, ?, ?, ?)",
        [job_id, actual_days, username, now()],
    )
    connection.commit()
    connection.close()


# --- Loading changes back ----------------------------------------------------

def replay_history(db_file, tracker):
    """Do every saved change again on the tracker. Returns how many were replayed.

    Order matters: a job has to be opened before it gets delays, and the
    tracker refuses delays on a closed job. So: all opens, then all delays
    (oldest first), then all closes.
    """
    connection = sqlite3.connect(db_file)
    opened = connection.execute(
        "SELECT job_id, asset, planned_days FROM jobs_opened ORDER BY opened_at").fetchall()
    delays = connection.execute(
        "SELECT job_id, logged_on_day, category, description, days_added, logged_by "
        "FROM delays_logged ORDER BY id").fetchall()
    closed = connection.execute(
        "SELECT job_id, actual_days FROM jobs_closed ORDER BY closed_at").fetchall()
    connection.close()

    # fetchall() gives a list of rows, and each row is a tuple, so
    # "for job_id, asset, planned_days in opened" unpacks one row at a time.
    was_quiet = tracker.quiet
    tracker.quiet = True
    for job_id, asset, planned_days in opened:
        tracker.create_job(job_id, asset, planned_days)
    for job_id, day, category, description, days_added, logged_by in delays:
        tracker.log_delay(job_id, day, category, description, days_added, logged_by=logged_by)
    for job_id, actual_days in closed:
        tracker.close_job(job_id, actual_days)
    tracker.quiet = was_quiet

    return len(opened) + len(delays) + len(closed)


if __name__ == "__main__":
    # Quick look at what's saved:  python database.py
    for db_file in [MAIN_DB, DEMO_DB]:
        if not os.path.exists(db_file):
            print(os.path.basename(db_file), "doesn't exist yet")
            continue
        connection = sqlite3.connect(db_file)
        print(os.path.basename(db_file))
        for table in ["jobs_opened", "delays_logged", "jobs_closed"]:
            count = connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            print(f"  {table}: {count} rows")
        connection.close()
