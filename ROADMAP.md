# Roadmap

The project is a general maintenance delay tracker, built in phases. Each phase ends with something that runs, and each one builds on the last instead of replacing it.

**Current focus: finishing the tracker**, with Tinker's depot delays (from the GAO report) as the main case study: cleaned data, results, a database, user accounts, and a web interface. The Navy case study already runs (in plain Python) and is on hold until the tracker is finished (Phase 9).

One rule across every phase: be able to explain every line out loud. Scholar's Day judges score "Depth of Understanding" and will ask questions. If a piece of code can't be explained, it isn't finished yet.

## Phase 0 — Groundwork

- [x] Define the case study problem from GAO-26-107890 (Recommendations 1, 6, and 7)
- [x] Write the README and design rationale
- [x] Secure a Scholar's Day faculty mentor (Prof. Kagitha)
- [x] Meet with the mentor
- [x] Register for Scholar's Day
- [x] Reframe the project as a general tool with Tinker as the case study
- [x] Received a dataset from the mentor (notes kept private, with the data)
- [x] Replied to the mentor about the dataset
- [x] Put the project on GitHub, with the dataset excluded ([jnguyen-tech/maintenance-delay-tracker](https://github.com/jnguyen-tech/maintenance-delay-tracker))
- [ ] Share the GitHub link and `schema.sql` with the mentor for feedback
- [x] Met with the mentor about the roadmap. He recommended the login system (admin, employee, manager) and a web interface: plain JavaScript first, then React, then animations.
- [x] Confirmed with the mentor how the dataset can be described publicly
- [ ] Mentor's email on data cleaning: agree on cleaning scope

## Phase 1 — Plain-Python prototype ✅

Prove the core logic works before any database is involved. Uses only lists, dictionaries, functions, loops, and math.

- [x] Jobs stored as a list of dictionaries
- [x] Estimates stored as append-only versions (version 1 = original plan, never overwritten)
- [x] Delay events with a set list of categories
- [x] Revision logic: every delay adds a new estimate version
- [x] Per-job report: original vs. current target, full history, slip by cause
- [x] Summary report: slip by cause across all jobs, and on-time counts against original vs. revised targets
- [x] Make the tool general: "asset" instead of "aircraft," and categories set per scenario
- [x] Move the Tinker scenario into its own file (`tinker_case_study.py`)
- [x] Second case study: Navy ship maintenance (`navy_case_study.py`), based on CBO (Dec. 2025) and GAO-20-588

## Phase 2 — Refactor into classes ✅

Rewrite `prototype.py` using classes (`Job`, `Estimate`, `DelayEvent`, and a `Tracker` that holds the lists and the categories).

- [x] Starter file with every class and method outlined (`maintenance_tracker.py`)
- [x] Answer key saved (`phase1_output.txt`) and checking tool written (`compare_outputs.py`)
- [x] Companion sheet written (`PHASE2_GUIDE.md`)
- [x] Learn classes, `__init__`, `self`, and imports (`PHASE2_GUIDE.md` Parts 1–4)
- [x] Steps 1–5: write every class and method
- [x] Step 6: switch `tinker_case_study.py` to the classes, then run `compare_outputs.py` until it says MATCH — **MATCH: all 67 lines identical**

(Step 7, switching the Navy case study to the classes, moved to Phase 9.)

## Phase 3 — Clean and load the dataset (in progress)

The dataset from the mentor (50,000 jobs, about 119,000 delays, about 182,000 estimate versions) is messy on purpose, so this phase is about cleaning it. The issue list is kept in private notes alongside the data.

- [x] Profile the data: what's in each file, how they connect, and what's wrong
- [x] Put the original files in `data/raw/` and never edit them by hand
- [x] Learn to read CSV files in Python with the built-in `csv` module (`read_jobs.py`: all 50,000 jobs read)
- [ ] Write the cleaning code in `cleaning.py`, working through the issue list:
  - [x] Step 2: dates in all 4 formats (200,000 dates parsed)
  - [x] Step 3: job IDs, depot names, and statuses (every delay row now finds its job)
  - [ ] Step 4: delay events — remove duplicates, map the 18 category spellings to 5, clean `days_added`
  - [ ] Recover the 1,187 missing or placeholder `days_added` values from the estimate history
  - [ ] Clean the estimate history (duplicates, `v1` versions, post-completion revisions)
  - [ ] Logic problems (non-closed jobs with completion dates, same-day jobs)
- [ ] Convert dates into calendar-day counts from each job's open date (all durations are calendar days)
- [ ] Show real dates in the reports: give each `Job` an `open_date`, add a helper that turns a day number into a date (open date + days, using Python's `datetime` module), and print both, like `Apr 2, 2024 (120 days)`. Day numbers stay underneath for the math. This changes the output on purpose, so save a new answer key afterward.
- [ ] Write the cleaned files to `data/clean/`
- [ ] Load the cleaned data into the tracker and run the reports
- [ ] Keep post-completion revisions in the history, but judge "on time" against the original and last regular targets

## Phase 4 — Results and visuals

Turn the results into something that reads well on a poster. This comes before the database on purpose: the poster needs results first, and the in-memory tracker can already produce them.

- [ ] Run the summary report on the cleaned dataset
- [ ] Chart: how many jobs look on time against the original target, the last regular target, and after post-completion revisions
- [ ] Chart: total slip by cause
- [ ] Chart: one job's timeline (for example `JOB-0000058`), showing how each revision moved the target
- [ ] Export the charts for the poster

## Phase 5 — Real database (SQLite)

Move the data from in-memory lists into a real database file, using Python's built-in `sqlite3` module.

- [ ] Learn the basics: primary keys, foreign keys, `INSERT`, `SELECT`, `WHERE`, `GROUP BY`
- [x] Draft the schema (`schema.sql`), including a table for each scenario's delay categories — review it with the mentor
- [ ] Add a `users` table, and a `logged_by` column on delays and estimates so every entry records who made it (needed for Phase 6)
- [ ] Write `db.py`: create the tables from `schema.sql`, then rewrite `create_job`, `log_delay`, `close_job`, and the reports to use SQL
- [ ] Load the cleaned data into the database
- [ ] Confirm the database blocks edits and deletes to history (the append-only triggers)

## Phase 6 — User accounts and roles

Add a login with three roles. Build and test it in Python from the command line first; the web interface comes after.

What each role can do:

| Action | Employee | Manager | Admin |
|---|:-:|:-:|:-:|
| View jobs and their full history | ✓ | ✓ | ✓ |
| Log a delay | ✓ | ✓ | |
| Open and close jobs | | ✓ | |
| View summary reports | | ✓ | ✓ |
| Create accounts and assign roles | | | ✓ |
| Set the list of delay categories | | | ✓ |
| Edit or delete history | ✗ | ✗ | ✗ |

The last row is the point: not even an admin can rewrite the record. Roles decide who can *add* to the history, and every addition is stamped with who made it.

- [ ] `users` table: username, hashed password, role, and an active flag (accounts are deactivated, never deleted, so old entries still show who made them)
- [ ] Never store plain passwords: hash them with a salt using Python's built-in `hashlib`
- [ ] `login(username, password)`: returns the user if the password matches, or `None` if not
- [ ] Permissions as a dictionary of role → allowed actions, plus a `can(user, action)` check at the top of every action
- [ ] Stamp every delay and estimate with `logged_by`
- [ ] Test each role from the command line (for example, an employee trying to close a job gets refused)
- [ ] Note for the poster: this is a demo login. Real Air Force systems use CAC cards and single sign-on, which this project doesn't attempt.

## Phase 7 — Web interface (JavaScript, then React, then animations)

Recommended by the mentor, in three steps. Each step works on its own before the next one starts. Python keeps doing the logic and the database the whole time; the web page only shows the data and sends what the user types.

**Step A — Plain HTML, CSS, and JavaScript.** No frameworks, and only the basics, so every piece can be explained.

- [ ] HTML basics: tags, headings, paragraphs, links, tables, forms, inputs, and buttons
- [ ] CSS basics: colors, fonts, spacing, and simple layouts
- [ ] JavaScript basics in the browser: finding elements on the page, responding to button clicks, and `fetch()` to ask Python for data
- [ ] Connect the page to Python with Flask (a small library that lets Python answer requests from a web page)
- [ ] Login page
- [ ] Job list: search by job ID, filter by depot and status
- [ ] Job page: original vs. current target, the full estimate history with real dates, and each delay with its cause and who logged it
- [ ] Log-a-delay form (employee and manager)
- [ ] Open and close jobs (manager)
- [ ] Reports page: the on-time comparison and slip by cause (manager and admin)
- [ ] Account management page (admin)
- [ ] Show only the buttons each role can use, but still check permissions in Python (hiding a button isn't security)

**Step B — Rebuild the pages in React.** React is a JavaScript library for building pages out of reusable pieces called components (for example, one `JobCard` component used for every job in the list). It's what most companies use, so it's a strong resume skill. Start only once Step A works, so there's a working version to compare against, the same way Phase 2 was checked against Phase 1.

- [ ] Learn React basics: components, props, state, and `useEffect` for loading data
- [ ] Rebuild the pages one at a time as components (login, job list, job page, forms, reports)
- [ ] Keep the same Python side; only the page changes

**Step C — Animations.** Animations aren't a separate language; they're done with CSS or a JavaScript library. Use them where they explain something, not just for decoration.

- [ ] CSS transitions for small touches (buttons, page changes, rows appearing)
- [ ] An animation library for bigger effects: Framer Motion (made for React) or GSAP
- [ ] The main one: an animated job timeline. The original target stays pinned in place while each delay pushes the current target further out, one revision at a time, with its cause labeled. It shows the project's whole point in a few seconds.

## Phase 8 — Scholar's Day

The poster uses the Phase 4 results, described the way the mentor approved. If the login and web interface are working by then, they become a live demo; if not, they go under "Next steps."

- [ ] Abstract (150–250 words), framed as tool + case study: question, why it matters, what was built, findings, implications
- [ ] Rough poster draft to the mentor
- [ ] Final poster (42" × 36", PowerPoint exported to PDF) using the Technical category sections: overview, goal, design process, technology, results, reflection
- [ ] Practice a 1–2 minute pitch and likely questions (for example: "Why not just use a spreadsheet?", "How would this connect to the Air Force's real systems?", "What else could this tool track?", "What if a worker's delay estimate is wrong?", and "Why can't an admin edit the history?")

## Phase 9 — After the tracker is finished

**Back to the Navy case study**

- [ ] Step 7 from Phase 2: switch `navy_case_study.py` to the classes. Same two-line change at the top, plus its extra report uses dictionary lookups (`job["status"]`, `estimates[i]["target_days"]`) that become fields (`job.status`, `estimates[i].target_days`)
- [ ] Run it through the database, login, and web interface
- [ ] Chart: average overrun against the class plan, first schedule, and final schedule

**Stretch goals**

- [ ] Optional third scenario outside defense (for example, airline engine repair or IT repair tickets)
- [ ] Work type: add a work-type field to jobs (for example scheduled overhaul, modification, or emergency) and report slip by work type, like real maintenance systems do. Needs data that includes work types.
- [ ] Estimate accuracy: record how long each delay actually took once fixed, and report how far off workers' estimates run for each category (for example, "discovered-work estimates run 40% low")
- [ ] Public demo deployment
- [ ] Short walkthrough video
- [ ] Resume and LinkedIn write-up; use the project when applying to 76 SMXG, depot-IT contractor, and aviation maintenance software roles
