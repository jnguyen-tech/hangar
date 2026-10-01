# Prototype Guide

A companion sheet for the two Python files. Keep it open next to the code.

- **`prototype.py`** is the general tool. It knows how to track jobs, estimates, and delays for any kind of asset, but it has no data of its own.
- **`tinker_case_study.py`** is the main scenario. It tells the tool which delay categories to use, then feeds in the Tinker jobs and delays and prints the reports.
- **`navy_case_study.py`** is a second scenario, for Navy ship overhauls, using the same tool.

This guide walks through `prototype.py` section by section in the same order as the file, then covers the two case study files.

## The big idea

A maintenance job gets a planned finish time. When something goes wrong — a mechanic finds corrosion, a part is late — the finish time moves out. Most systems just overwrite the old number. This tool never does. It adds a new estimate and keeps every old one, so you can always see the original plan, every change, and why each change happened.

The idea works for any kind of maintenance, so the tool uses the word "asset" instead of "aircraft." The Tinker case study is where it gets tested on a real problem: GAO report GAO-26-107890 found that when only the latest target date is kept, depot jobs can look on time even though they're far behind the original plan. The last lines of the case study output show exactly that happening.

Days are plain numbers ("day 0" is the day the job opened), so the math is just adding, subtracting, and percentages. They're calendar days: every day counts, including weekends and holidays.

## Python you'll see in these files

| Thing | Example | What it means |
|---|---|---|
| List | `jobs = []` | An ordered collection. Starts empty here. |
| `.append()` | `jobs.append(job)` | Adds an item to the end of a list. |
| `.clear()` | `categories.clear()` | Empties a list, so it has no items left. |
| Dictionary | `{"job_id": 1, "asset": "B-52H"}` | Labeled boxes, like one row of a spreadsheet. |
| Reading a dictionary | `job["asset"]` | Gets the value stored under that label. |
| `None` | `"actual_days": None` | Means "nothing here yet." |
| `[0]` and `[-1]` | `estimates[0]`, `estimates[-1]` | First item of a list, and last item of a list. |
| `+=` | `total += 5` | Shorthand for `total = total + 5`. |
| `len()` | `len(delay_events)` | How many items are in a list. |
| `in` | `if category not in categories:` | Checks whether a value is in a list. |
| Early `return` | `return` inside an `if` | Stops the function right there. Used after printing an error. |
| f-string | `f"Job {job_id} closed"` | A string with `{}` slots that get filled with values. |
| Quotes inside f-strings | `f"{job['asset']}"` | Use single quotes inside when the f-string uses double quotes. |
| Docstring | `"""Return the job..."""` | The first line inside a function. Describes what it does. |
| `import ... as` | `import prototype as tracker` | Loads another Python file so you can use its functions, under a nickname. |

## prototype.py, Section 1: Data

```python
jobs = []
estimates = []
delay_events = []
categories = ["discovered_work", "parts", "staffing", "other"]
```

The three lists are the "tables." They start empty and fill with dictionaries as the program runs. Note the direction: **lists hold dictionaries** here. The list is the whole table, and each dictionary inside it is one row, so `jobs[0]` is the first job and `jobs[0]["asset"]` is one value from it.

- `jobs` holds one dictionary per job — one asset being worked on.
- `estimates` holds one dictionary per version of a job's planned finish. A job starts with version 1 and gets another version every time it's delayed.
- `delay_events` holds one dictionary per problem that pushed a job's finish out.

`categories` is the list of allowed delay reasons. Having a set list is what makes the totals work. If people could type any reason, you'd end up with "parts," "Parts," and "waiting on part," and nothing would add up.

The four categories above are just defaults. Different kinds of maintenance have different causes of delay, so a scenario can swap in its own list with **`set_categories(new_categories)`**. It empties the list with `.clear()`, then appends each new category. It should be called before any delays are logged.

## Section 2: Small helpers

These are small tools the rest of the file reuses, so the same loop isn't written over and over.

**`rows_for_job(table, job_id)`** loops through any of the lists and returns a new list with only the rows for one job. `table` can be `estimates` or `delay_events` — the same function works for both because both kinds of dictionaries have a `"job_id"` label.

**`total_days_by_category(events)`** adds up delay days per category. It starts every category at 0, then goes through each event and adds its days to that event's category:

```python
totals[event["category"]] += event["days_added"]
```

If the event is `{"category": "parts", "days_added": 10}`, that line becomes `totals["parts"] += 10`. It returns a dictionary like `{"discovered_work": 35, "parts": 10, "staffing": 5, "other": 0}`.

**`percent(part, whole)`** returns `part` as a percentage of `whole`, rounded to one decimal place. If `whole` is 0, it returns 0 instead of crashing, because dividing by zero is an error in Python.

## Section 3: Jobs

**`find_job(job_id)`** loops through `jobs` and returns the matching job, or `None` if there isn't one. Almost every other function calls this first to make sure the job exists.

**`create_job(job_id, asset, planned_days)`** does two things:

1. Adds the job to `jobs`, with status `"open"`.
2. Adds the job's first estimate to `estimates` as version 1, with the reason "original plan."

That first estimate is the most important record in the tool. It never changes. In the Tinker case study, it's the number GAO Recommendation 1 says the Air Force should report.

**`close_job(job_id, actual_days)`** finds the job and changes two of its values: the status becomes `"closed"`, and `actual_days` records how long the job really took.

## Section 4: Estimates

This section is the core of the project. Its rule: **add new versions, never change old ones.**

**`get_estimates_for_job(job_id)`** returns every estimate for one job, oldest first (they come out in the order they were added).

**`get_original_estimate(job_id)`** returns the first one: `[0]`.

**`get_current_estimate(job_id)`** returns the last one: `[-1]`.

**`revise_estimate(job_id, delay_event)`** builds the next version from the current one:

```python
"version": current["version"] + 1,
"target_days": current["target_days"] + delay_event["days_added"],
```

So if the current plan is version 1 at 120 days and a delay adds 15, the new estimate is version 2 at 135 days. It's added with `.append()`. The old estimate is never touched.

## Section 5: Delay events

**`get_delays_for_job(job_id)`** returns every delay for one job, the same way `get_estimates_for_job` does.

**`log_delay(job_id, logged_on_day, category, description, days_added)`** is what you call when something goes wrong. `days_added` is the workers' estimate of how much time the problem adds — for example, a mechanic judging that a corrosion repair will take about 15 more days. The tool doesn't guess delays; it records those estimates and adds them up. If an estimate turns out wrong, you log another delay for the difference (like "repair took longer than expected, +7 days"), so both the first estimate and the correction stay on record.

It runs in four steps:

1. **Check the job exists.** If not, print an error and stop.
2. **Check the category is allowed.** If it isn't in `categories`, print an error and stop. This is why the case study's `"bad_category"` line gets rejected.
3. **Build and save the event.** Its ID is `len(delay_events) + 1`, so the first event is 1, the second is 2, and so on.
4. **Call `revise_estimate`.** Logging a delay automatically creates the new estimate version. There's no way to record a delay without the plan updating.

## Section 6: Reports

**`print_job_report(job_id)`** covers one job:

- The original target, the current target, and the slip between them.
- The full estimate history, one line per version.
- Slip by cause, using `total_days_by_category`. Categories with 0 days are skipped. If there are no delays at all, it says so.
- The actual finish time, if the job is closed.

**`print_slip_by_cause()`** does the same cause breakdown, but across every job at once, and shows each cause as a percentage of the total.

**`print_on_time_comparison()`** makes the tool's main point. It first collects the closed jobs, then asks two questions about each one:

- Did it finish by its **original** target?
- Did it finish by its **revised** (current) target?

It counts the yeses for each question. The difference between the two counts is the number of jobs that "only look on time because the target moved."

**`print_summary_report()`** prints a header and calls the two functions above. Splitting it up this way means the summary reads like a table of contents.

**The last lines of the file** only run if you run `prototype.py` directly. Because the tool has no data of its own, all they do is tell you to run the case study instead.

## tinker_case_study.py: the scenario

This file has no tracking logic. It borrows everything from the tool:

```python
import prototype as tracker
```

That line loads `prototype.py` and gives it the nickname `tracker`. After that, every tool function is called with `tracker.` in front, like `tracker.create_job(...)`. The `tracker.` prefix makes it obvious which code belongs to the tool and which belongs to the scenario.

If imports are new to you, Part 4 of `PHASE2_GUIDE.md` explains them from scratch.

**`TINKER_CATEGORIES`** is the case study's list of delay causes: discovered work, parts, staffing, and other. These match the drivers of depot delays that GAO discusses.

**`run_case_study()`** does the whole scenario in order:

1. Prints a header saying this is the Tinker case study and that the data is synthetic.
2. Calls `tracker.set_categories(TINKER_CATEGORIES)`.
3. Opens three jobs on real aircraft types that go through depot maintenance at Tinker (B-52H, B-1B, KC-135). The jobs themselves are made up.
4. Logs the delays, including one bad category to show the error check.
5. Closes the jobs and prints every report.

```python
if __name__ == "__main__":
    run_case_study()
```

This runs the case study only when you run the file directly with `python3 tinker_case_study.py`. Another file could import it without re-running everything.

Splitting things this way is what makes the tool general. A different scenario, like an IT repair desk, would be its own file with its own categories and jobs, using the exact same `prototype.py`.

## navy_case_study.py: the second scenario

This file works exactly like the Tinker one — `import prototype as tracker`, then `set_categories`, `create_job`, `log_delay`, `close_job`, and the reports — but for Navy ship overhauls. It's based on a December 2025 Congressional Budget Office report and GAO-20-588. The ship types are real; every overhaul and number is made up.

Three things are new:

**1. Planning estimates become versions.** The Navy estimates each overhaul several times before it starts: a class plan, then a first schedule about two years out, then a final schedule 4–6 months out. The class plan is version 1 (from `create_job`), and each later schedule is logged with the category `"planning_revision"`, so it becomes version 2 and version 3. No new tool code was needed — the scenario just uses `log_delay` for a different kind of change.

**2. Negative days.** Day 0 is the day the overhaul starts, so the planning revisions are logged on day -730 (about two years before) and day -150 (about five months before). The tool doesn't care whether a day number is negative; it just stores and prints it.

**3. An extra report, `print_estimate_comparison(tracker)`.** This is the one piece of new logic. It takes the tracker as a parameter, and for each closed ship, it compares the actual duration against each of the first three estimates:

```python
for i in range(len(PLANNING_ESTIMATES)):
    planned = estimates[i]["target_days"]
    overrun = tracker.percent(actual - planned, planned)
```

`PLANNING_ESTIMATES` is `["class plan", "first schedule", "final schedule"]`, so `i = 0` looks at version 1, `i = 1` at version 2, and `i = 2` at version 3. It also keeps a running total for each estimate in `overrun_totals` (a list of three numbers) so it can print the average across all ships at the end.

The result shows CBO's finding in miniature: the average ship ran about 63% longer than its first schedule, but only about 30% longer than its final schedule. Same ships, same actual days — the "how late" number depends entirely on which estimate you compare against.

Be clear about this if anyone asks: the made-up numbers were chosen so the averages land near CBO's real ones. The tool didn't discover the 63% — it shows how the comparison works.

## Traced example: one delay, step by step

What happens when the case study runs `tracker.log_delay(1, 20, "discovered_work", "Corrosion found on wing spar", 15)`:

1. `find_job(1)` finds the B-52H job, so it continues.
2. `"discovered_work"` is in `categories` (the case study set it), so it continues.
3. `delay_events` is empty, so `len(delay_events) + 1` is 1. The event gets ID 1 and is appended.
4. `revise_estimate(1, event)` runs:
   - `get_current_estimate(1)` returns version 1 at 120 days.
   - The new estimate is version `1 + 1 = 2`, with a target of `120 + 15 = 135` days, reason "Corrosion found on wing spar."
   - It's appended. `estimates` now holds version 1 (120) and version 2 (135) for job 1.
5. It prints `Job 1, day 20: discovered_work (+15 days) - Corrosion found on wing spar`.

Later, the `"parts"` delay adds 10 more days, creating version 3 at 145. Job 1 then closes at 145 days. Against its revised target of 145 it's on time; against its original target of 120 it's 25 days late. That's the whole project in one job.

## How the pieces connect

```
tinker_case_study.py
  set_categories ──> chooses the allowed delay causes
  create_job ──────> adds a job + estimate version 1
  log_delay ───────> adds a delay event
                └──> revise_estimate ──> adds the next estimate version
  close_job ───────> records the actual finish
  print reports ───> read the lists and do the math

(every function above lives in prototype.py)
```

Everything flows into the three lists. The reports only read them; they never change anything.

## Check yourself

Try these before looking at the answers.

1. Why does `revise_estimate` use `.append()` instead of changing `current["target_days"]` directly?
2. If you added `tracker.log_delay(3, 10, "parts", "Missing bolts", 4)` to the case study, what would job 3's current target be, and what version number would it have?
3. Job 2 finished in 118 days, and its revised target was 115. Does it count as on time against its revised target?
4. What would `percent(10, 50)` return?
5. Why does `rows_for_job` work for both `estimates` and `delay_events`?
6. An IT repair scenario calls `set_categories(["waiting_on_user", "parts"])`, then tries to log a `"staffing"` delay. What happens?
7. In the Navy case study, destroyer A's final schedule was 220 days and it actually took 285. What does the report print for "vs final schedule"?

### Answers

1. Changing it would erase the history. Appending keeps the original plan and every revision on record, which is the entire point of the project.
2. 104 days (100 + 4), as version 2.
3. No. 118 is more than 115, so job 2 is late against both its revised and original targets. That's why only 2 of 3 jobs count as on time against revised targets.
4. `20.0`
5. Every dictionary in both lists has a `"job_id"` label, and that's the only label `rows_for_job` looks at.
6. It's rejected with an error message, because `"staffing"` isn't in that scenario's list of categories. No event is saved and no new estimate is created.
7. `29.5% longer`. The overrun is 285 − 220 = 65 days, and 65 ÷ 220 × 100 = 29.5.
