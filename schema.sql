-- schema.sql
--
-- Phase 5 design: the tables from prototype.py, as real SQLite tables.
-- Load it from Python with the built-in sqlite3 module (nothing to install):
--
--     import sqlite3
--     conn = sqlite3.connect("tracker.db")
--     conn.executescript(open("schema.sql").read())
--
-- Differences from prototype.py:
--   * Dates are real dates stored as text ('2026-10-01') instead of day numbers.
--   * The database itself enforces the rules (valid categories, append-only history),
--     so a bug in the Python code can't quietly break them.
--   * Delay categories live in their own table, so each scenario (the Tinker case
--     study, or any other) can load its own list without changing this file.

PRAGMA foreign_keys = ON;  -- SQLite only checks REFERENCES links when this is on


-- The allowed reasons for a delay. A scenario inserts its own rows here.
CREATE TABLE IF NOT EXISTS delay_categories (
    category  TEXT PRIMARY KEY
);


-- One row per maintenance job. An "asset" can be an aircraft, vehicle, building, etc.
CREATE TABLE IF NOT EXISTS jobs (
    job_id      INTEGER PRIMARY KEY,
    asset       TEXT NOT NULL,
    status      TEXT NOT NULL DEFAULT 'open' CHECK (status IN ('open', 'closed')),
    opened_on   TEXT NOT NULL,   -- e.g. '2026-10-01'
    closed_on   TEXT             -- stays NULL until the job closes
);


-- One row per thing that pushed a job's completion date out.
CREATE TABLE IF NOT EXISTS delay_events (
    event_id     INTEGER PRIMARY KEY,
    job_id       INTEGER NOT NULL REFERENCES jobs(job_id),
    category     TEXT    NOT NULL REFERENCES delay_categories(category),
    description  TEXT    NOT NULL,
    logged_on    TEXT    NOT NULL,
    days_added   INTEGER NOT NULL CHECK (days_added >= 0)
);


-- One row per VERSION of a job's target completion date.
-- Version 1 is the original plan; every delay adds a new version.
CREATE TABLE IF NOT EXISTS estimates (
    estimate_id     INTEGER PRIMARY KEY,
    job_id          INTEGER NOT NULL REFERENCES jobs(job_id),
    version         INTEGER NOT NULL,
    target_date     TEXT    NOT NULL,
    created_on      TEXT    NOT NULL,
    delay_event_id  INTEGER REFERENCES delay_events(event_id),  -- NULL for version 1
    UNIQUE (job_id, version)  -- a job can't have two "version 2"s
);


-- Append-only rules: history can be added to, never edited or deleted.
-- If anything tries, SQLite cancels it with an error message.
CREATE TRIGGER IF NOT EXISTS estimates_no_update BEFORE UPDATE ON estimates
BEGIN
    SELECT RAISE(ABORT, 'estimates are append-only: insert a new version instead');
END;

CREATE TRIGGER IF NOT EXISTS estimates_no_delete BEFORE DELETE ON estimates
BEGIN
    SELECT RAISE(ABORT, 'estimates are append-only: history cannot be deleted');
END;

CREATE TRIGGER IF NOT EXISTS delay_events_no_update BEFORE UPDATE ON delay_events
BEGIN
    SELECT RAISE(ABORT, 'delay events are append-only');
END;

CREATE TRIGGER IF NOT EXISTS delay_events_no_delete BEFORE DELETE ON delay_events
BEGIN
    SELECT RAISE(ABORT, 'delay events are append-only');
END;


-- Example: loading the Tinker case study's categories (run once per database):
--   INSERT INTO delay_categories (category)
--   VALUES ('discovered_work'), ('parts'), ('staffing'), ('other');
--
-- Example queries:
--
-- A job's original target (what GAO Recommendation 1 says to report):
--   SELECT target_date FROM estimates WHERE job_id = 1 AND version = 1;
--
-- A job's current target:
--   SELECT target_date FROM estimates WHERE job_id = 1 ORDER BY version DESC LIMIT 1;
--
-- Total days of slip by cause across all jobs:
--   SELECT category, SUM(days_added) FROM delay_events GROUP BY category;
