# Maintenance Delay Tracker

John Nguyen, Oklahoma City Community College

A general-purpose tool for tracking maintenance delays honestly: it keeps the original plan on record instead of overwriting it. Its main case study, built from a public GAO report, is depot maintenance delays at Tinker AFB. A second case study on Navy ship maintenance shows the same tool works elsewhere.

> **Status:** Demo / portfolio project. It runs entirely on synthetic data and is not connected to, and does not represent, any real Air Force, Navy, or other maintenance system or records.

## The idea

Maintenance jobs slip. A mechanic opens something up and finds damage nobody planned for, a part is late, or a crew is short-handed. When that happens, the planned finish date gets pushed out. If only the latest date is kept, the original plan disappears, and with it the record of how late the job really is.

This tool never overwrites. Every delay is logged with its cause, and every change to the planned finish is saved as a new version. So at any point you can see the original plan, every revision, why each one happened, and how late the job is compared to what was first promised.

The idea isn't specific to aircraft. An "asset" in this tool can be an aircraft, a ship, a vehicle, or a computer, and each scenario chooses its own delay categories.

## What this project solves

**In one sentence:** it's a tool that tracks maintenance delays honestly, so jobs can't look on time just because their deadline kept moving, and you can see what caused each delay.

It's a **measurement problem**: how to track delays so they can't be hidden. When only the newest finish date is kept, a job can look on time even though it's far behind what was first promised, and nobody can tell why it slipped. GAO found this at Tinker, and CBO found the same pattern with Navy ships.

The tool addresses it in three ways:

1. **It keeps the original plan.** Every change to the finish date is saved as a new version, so you can always compare against what was first promised.
2. **It records why each delay happened.** Each delay is logged with its cause, like discovered damage, parts, or staffing, at the moment it's found.
3. **It shows the gap.** The reports show how many jobs look on time only because their target moved.

**What it doesn't solve:** the delays themselves. It doesn't make repairs faster or fix parts or worker shortages. It makes lateness visible and explainable, which is the first step before anyone can fix it.

## What the tool does

- Tracks maintenance jobs on any asset, from open to close.
- Records every revision to a job's target completion as its own entry — never overwrites a prior estimate.
- Logs each delay with a category, a description, and the workers' estimate of how many days it adds. Categories are set per scenario.
- Reports, per job or rolled up across all jobs, the gap between the original estimate and the current one, broken down by cause.
- Compares how many jobs count as "on time" against their original targets versus their revised targets — showing how revised targets can hide lateness.

All durations are **calendar days**: every day counts, including weekends and holidays. Working days would make the same delays look smaller, and a completion date is a calendar date — the day the asset is back in service.

## What's being built next

**User accounts with three roles.** Each person logs in as an employee, a manager, or an admin, and every delay and estimate is stamped with who entered it.

| Action | Employee | Manager | Admin |
|---|:-:|:-:|:-:|
| View jobs and their full history | ✓ | ✓ | ✓ |
| Log a delay | ✓ | ✓ | |
| Open and close jobs | | ✓ | |
| View summary reports | | ✓ | ✓ |
| Create accounts and set delay categories | | | ✓ |
| Edit or delete history | ✗ | ✗ | ✗ |

No role can rewrite the record, not even an admin. Roles decide who can add to the history, never who can change it. (This is a demo login; real Air Force systems use CAC cards and single sign-on.)

**A web interface**, so the tracker can be used from a browser instead of the command line: a job list, a page for each job's full history, a form for logging delays, and the reports. It's built in three steps: plain HTML, CSS, and JavaScript first, then rebuilt in React, then animations, including an animated timeline that shows a job's target date sliding out with each delay while the original stays pinned. Python keeps handling the logic and the database.

## Running it

Python 3 is the only requirement; nothing else needs to be installed. From the project folder, run:

```
python3 tinker_case_study.py
```

(On Windows, type `python` instead of `python3`.)

This loads the Tinker scenario, opens three sample jobs, logs delays against them, closes them, and prints a report for each job plus a summary. The summary ends with the project's core point:

```
Closed jobs: 3
  On time measured against REVISED targets:  2 of 3
  On time measured against ORIGINAL targets: 1 of 3
  Jobs that only look on time because the target moved: 1
```

The sample data is made up to illustrate the pattern. To run the second case study:

```
python3 navy_case_study.py
```

Its last section compares each ship's actual overhaul length against three different planning estimates.

## Case study 1: Tinker's depot delays

In May 2026, GAO published [*Air Force Readiness: Actions Needed to Address Depot Maintenance Delays and Staffing Challenges*](https://www.gao.gov/products/gao-26-107890) (GAO-26-107890), reviewing the Air Force's three maintenance depots, including Oklahoma City Air Logistics Complex at Tinker AFB. The report identifies two problems:

1. Maintenance delays at the depots are increasing, which reduces aircraft availability for training and operations.
2. The Air Force's way of tracking timeliness doesn't show the full extent of those delays. Jobs are measured against target completion dates that get revised as work slips, so a job can look on time against its latest target while running well behind its original one. The Air Force also doesn't fully capture how much delay comes from **unplanned work discovered mid-maintenance** — for example, a mechanic opens up an aircraft and finds corrosion or a cracked part nobody expected.

The second finding is what this project tests against.

GAO made 10 recommendations; DoD agreed to 8 and partially agreed to 2. Two of them are directly relevant here:

- **Recommendation 1 (agreed):** use the *original* target completion date, not the revised one, as the primary metric for reporting depot maintenance timeliness. The tool's estimate history, which never overwrites the original, is built to support exactly this.
- **Recommendations 6 & 7 (partially agreed):** capture unplanned-work delays for root-cause trend analysis. DoD agreed the data should be captured but disagreed with GAO on *where and how* to capture it within existing systems — this is still an open implementation question.

## Case study 2: Navy ship maintenance

*This case study runs in the plain-Python version of the tool. It's on hold while the tracker is finished around the Tinker case study, and will be moved onto the finished version afterward.*

To show the tool isn't tied to one situation, it's also tested on an independent scenario: maintenance delays for conventional Navy ships.

The Congressional Budget Office's [*Maintenance Delays for Conventional Navy Ships*](https://www.cbo.gov/publication/61940) (December 2025) found that the Navy makes several estimates for each overhaul — a class plan, a first schedule about two years out, and a final schedule 4–6 months out — and that how late a ship looks depends on which one you compare against. Overhauls lasted 63% longer than first schedules on average, but only about 15–60% longer than final schedules. Overhauls with new or growth work (work discovered once the ship is in the shipyard) took nearly 30% longer. GAO's earlier report on aircraft carriers and submarines, [GAO-20-588](https://www.gao.gov/products/gao-20-588), found that 38 of 51 maintenance periods finished late, with unplanned work contributing more than 4,100 days of delay.

It's the same pattern as Tinker: the later the estimate you measure against, the less late a job looks. The Navy scenario stores each planning estimate as its own version, then compares every ship's actual duration against all three. Its synthetic numbers were chosen to land near CBO's averages — about 63% longer than first schedules and 30% longer than final schedules — so the result shows the comparison working. It isn't new evidence.

## Why the design looks this way

Each design decision below traces back to the problems in the case studies.

- **Estimates are versioned, not overwritten.** Each job keeps one record per *revision* to its target completion, each linked to the delay that caused it. GAO found that reporting against only the latest target date hides the full extent of delays. Keeping version 1 unchanged preserves the original target that Recommendation 1 says to report.
- **Delays are categorized when they're discovered.** Every event that pushes a date out is logged with a cause and a time when it happens, not reconstructed afterward. That's what makes a "how much of the delay was discovered work?" breakdown possible, and it's one candidate answer to the open question in Recommendations 6 & 7 — this project's proposal, not an official one.
- **Nothing is deleted or edited in place.** The estimate history and delay log are append-only, so the reported timeline can always be traced back to the records behind it. In the database version (`schema.sql`), the database itself blocks edits and deletes to that history.
- **Categories are data, not code.** Each scenario supplies its own list of delay causes, so the same tool works for a depot, a shipyard, or an IT repair desk without changing the core logic.

## Data model (overview)

| Table | Purpose |
|---|---|
| `jobs` | One row per maintenance job: asset, open date, current status |
| `estimates` | One row per revision to a job's target completion; links to the triggering delay; never overwritten |
| `delay_events` | One row per delay: job, category, description, date logged, days added |
| `delay_categories` | The allowed delay causes for the scenario being tracked |

*(Full schema with field-level detail lives in `schema.sql`.)*

## Tech stack

- Python 3, standard library only for now — no installs needed
- A 50,000-job practice dataset (synthetic, provided by the faculty mentor), cleaned with Python's built-in `csv` and `datetime` modules so the case study can be demoed at scale (Phase 3; see `DATA_GUIDE.md`)
- SQLite through Python's built-in `sqlite3` module for storage (Phase 5)
- Password hashing with Python's built-in `hashlib` for the login (Phase 6)
- Plain HTML, CSS, and JavaScript for the web interface, connected to Python with Flask, then React, with CSS and Framer Motion or GSAP for animations (Phase 7)

## Project structure

```
maintenance-delay-tracker/
├── README.md               # this file
├── ROADMAP.md              # phase-by-phase plan and progress checklist
│
│   The tool and its case studies
├── prototype.py            # the original plain-Python version (Phase 1); the Navy case study still uses it
├── tinker_case_study.py    # case study 1: Tinker depot delays
├── navy_case_study.py      # case study 2: Navy ship overhauls
├── maintenance_tracker.py  # the tool rewritten with classes (Phase 2); the Tinker case study runs on this
├── schema.sql              # Phase 5 design: the SQLite tables, with append-only rules
│
│   Cleaning the practice dataset (Phase 3, in progress)
├── read_jobs.py            # first look at the jobs file: prints 5 rows and the total
├── cleaning.py             # cleaning functions (dates, IDs, depots, statuses, delays), with tests
│
│   Study guides and checking tools
├── PROTOTYPE_GUIDE.md      # plain-language walkthrough of the Phase 1 code
├── PHASE2_GUIDE.md         # classes, __init__, self, imports, and the Phase 2 steps
├── DATA_GUIDE.md           # the mentor's practice dataset: files, links, and cleaning checklist
├── compare_outputs.py      # confirms Phase 2 output matches Phase 1
├── phase1_output.txt       # the Phase 1 output, used as the answer key
│
└── data/                   # not on GitHub (see below)
    ├── raw/                # the dataset's original files, never edited
    └── clean/              # cleaned files written by the code
```

### Getting the data

The practice dataset isn't included in this repository. It was shared by the faculty mentor for coursework, so it isn't mine to publish. The case studies and the Phase 2 check (`compare_outputs.py`) don't need it.

To run the cleaning code, put the dataset's files in `data/raw/`:

```
data/raw/
├── maintenance_jobs_export.csv
├── delay_events_legacy.csv
├── delay_events_2024.csv
├── delay_events_current.csv
├── target_estimate_history.csv
├── maintenance_delay_notes.txt
└── README.txt
```

Then run `python cleaning.py`. `DATA_GUIDE.md` describes each file and the cleaning checklist.

## Progress

Phases 1 and 2 are complete: the plain-Python tool works, and it has been rewritten with classes in `maintenance_tracker.py`, with output that matches the original line for line. The current focus is the Tinker case study. Phase 3, cleaning the mentor's 50,000-job practice dataset, is underway in `cleaning.py`: dates in all four formats now parse, and job IDs, depot names, and statuses are standardized, with every delay row now matching its job. Next come the Tinker results and charts, the SQLite database, user accounts with roles, and a JavaScript web interface. See [ROADMAP.md](ROADMAP.md) for the full checklist.

## Presenting this project

This project is being prepared for **OCCC Scholar's Day** (November 17, 2026), in the Technical project category. The poster will follow the same structure as this README — the tool, the case studies, design decisions, technology, results, and reflection.

## What this is (and isn't)

To be direct about scope: this project does not solve the Air Force's or the Navy's problem, and it isn't the first attempt to address either one.

The Air Force already runs enterprise systems (IMDS and related depot maintenance data systems) that track job status and completion dates in some form. The gap GAO identified is a reporting and data-governance problem — which number counts as the "real" target date, and how unplanned work gets attributed — layered on top of those existing systems, not a case of no software existing at all. The actual fix, whenever it's implemented, will be built by AFMC program offices and their support contractors, working against real depot data with real security constraints this project has no access to and doesn't attempt to replicate.

What this project actually is: a general maintenance delay tracker, tested on realistic scenarios built from public GAO and CBO reports. It's a working, defensible answer to a clearly defined design problem — a candidate implementation of GAO's Recommendation 1 and one possible answer to the open question in Recommendations 6 & 7. The value is in showing the ability to read a real problem statement and turn it into working software, not in claiming to have solved something nobody else is working on.

## Why this project

Built as a portfolio piece aimed at maintenance and sustainment software roles — the systems that manage maintenance workflows and readiness tracking, as distinct from avionics or flight-systems work. The Tinker case study targets depot IT work at Tinker AFB (76 SMXG) and the contractor ecosystem that supports it, while the general design applies equally to civilian aviation maintenance tracking, including FAA-regulated maintenance.
