# Phase 2 Guide

A companion sheet for `maintenance_tracker.py`. Keep it open while you fill in the classes.

Phase 2 rebuilds the same tool using classes. It adds no new features: when you're done, the Tinker case study should print exactly what it printed in Phase 1. `compare_outputs.py` checks that for you.

## Part 1: Lists hold dictionaries → lists hold objects

In Phase 1, **lists hold dictionaries**. The list is the whole table, and each dictionary is one row:

```python
jobs = [
    {"job_id": 1, "asset": "B-52H", "status": "open"},
    {"job_id": 2, "asset": "B-1B",  "status": "open"},
]
jobs[0]["asset"]    # "B-52H"
```

In Phase 2, **lists hold objects**. Each dictionary becomes an object made from a class, and labels become fields:

```python
jobs = [Job(1, "B-52H"), Job(2, "B-1B")]
jobs[0].asset       # "B-52H"
```

Same shape, same data. The only visible change is `["asset"]` becoming `.asset`.

(Dictionaries *can* hold lists, like `{"versions": [120, 135, 145]}`, but this project doesn't use that shape. The only dictionary left in Phase 2 is `totals` in `total_days_by_category`.)

## Part 2: Classes, objects, `__init__`, and `self`

**A class is a blueprint. An object is one thing built from it.** `Job` is the blueprint; `Job(1, "B-52H")` builds one job object.

**`__init__` is the setup method.** Python runs it automatically every time you build an object. You never call it by name.

```python
class Job:
    def __init__(self, job_id, asset):
        self.job_id = job_id
        self.asset = asset
        self.status = "open"
        self.actual_days = None

job = Job(1, "B-52H")    # __init__ runs right here
```

On that last line, Python:

1. Builds a new, empty `Job` object.
2. Runs `__init__`, with the new object as `self`, `1` as `job_id`, and `"B-52H"` as `asset`.
3. Each `self.something = ...` line stores a field on the object.

Some fields come from what you pass in (`job_id`, `asset`). Others always start the same way (`status` starts as `"open"`).

**`self` means "this particular object."** Two jobs never get mixed up, because each has its own `self.asset`.

**Methods are functions that live inside a class.** Their first parameter is always `self`. When you call a method on an object, Python fills in `self` for you:

```python
t = Tracker()
t.find_job(1)     # Python runs find_job with self = t and job_id = 1
```

Inside a method, you use `self.` to reach the object's fields and its other methods:

```python
self.jobs              # this tracker's job list
self.find_job(job_id)  # call another method on this same tracker
```

**Why `Tracker` holds the lists:** in Phase 1, the lists are global, so the whole program shares one set. If you loaded two scenarios at once, their jobs would mix. In Phase 2, every `Tracker()` gets its own lists in `__init__`, so each scenario stays separate.

## Part 3: Translation cheat sheet

Use this to turn each `prototype.py` function into a method.

| Phase 1 (`prototype.py`) | Phase 2 (`maintenance_tracker.py`) |
|---|---|
| `jobs = []` at the top of the file | `self.jobs = []` inside `Tracker.__init__` |
| `categories` | `self.categories` |
| `def find_job(job_id):` | `def find_job(self, job_id):` |
| `find_job(job_id)` inside another function | `self.find_job(job_id)` inside another method |
| `job["asset"]` | `job.asset` |
| `f"{job['asset']}"` | `f"{job.asset}"` |
| `jobs.append({"job_id": job_id, ...})` | `self.jobs.append(Job(job_id, asset))` |
| `estimates.append({...})` | `self.estimates.append(Estimate(...))` |
| `percent(slip, original)` | `percent(slip, original)` — unchanged, it's a plain function |

**Worked example: `find_job`.** This is the pattern for every method.

```python
# Phase 1
def find_job(job_id):
    for job in jobs:
        if job["job_id"] == job_id:
            return job
    return None

# Phase 2
def find_job(self, job_id):
    for job in self.jobs:
        if job.job_id == job_id:
            return job
    return None
```

Three changes: `self` added to the parameters, `jobs` became `self.jobs`, and `job["job_id"]` became `job.job_id`. The logic is identical.

## Part 4: Imports, from scratch

**`import` lets one Python file use code from another file.** Without it, every file would have to contain all of its own code.

There are three ways to write it, and this project uses all three.

**1. `import name`**: load a whole file (called a *module*) and use its code with the module's name in front.

```python
import prototype
prototype.create_job(1, "B-52H", 120)
```

**2. `import name as nickname`**: the same thing, with a shorter or clearer name. This is what `tinker_case_study.py` does now:

```python
import prototype as tracker
tracker.create_job(1, "B-52H", 120)
```

**3. `from name import Thing`**: pull in one specific thing, so you can use it without the prefix. This is what you'll switch the case study to in Step 6:

```python
from maintenance_tracker import Tracker
tracker = Tracker()
tracker.create_job(1, "B-52H", 120)
```

Rules to know:

- **No `.py`.** The file is `maintenance_tracker.py`, but you write `import maintenance_tracker`.
- **Several at once.** Separate names with commas: `from maintenance_tracker import Tracker, percent`.
- **Same folder.** Your own files can import each other when they're in the same folder, and you run Python from that folder.
- **Imports go at the top** of the file.
- **Importing runs the file.** Python runs the imported file's top-level code once. That's why each file puts its demo or tests under `if __name__ == "__main__":` — that block runs only when you run the file directly, not when it's imported.

Python also comes with built-in modules you import the same way. You'll meet them in later phases:

- `sqlite3` (Phase 5) for the database
- `csv` or `pandas` (Phase 3) for reading and cleaning the mentor's dataset. `csv` comes with Python; `pandas` has to be installed.
- `matplotlib` (Phase 4) for charts. This one doesn't come with Python and has to be installed first.

`compare_outputs.py` imports `subprocess` and `sys` so it can run the case study and read what it prints. It's a checking tool, not part of the project, so you don't need to understand those two.

## Part 5: Working through the steps

The test lines are at the bottom of `maintenance_tracker.py`. After finishing each step, remove the `#` from that step's lines and run:

```
python3 maintenance_tracker.py
```

(On Windows, it may be `python` instead of `python3`.)

Keep earlier steps' test lines uncommented. Each step builds on the one before, so the output below includes the earlier lines too.

**Step 1: `Estimate.__init__` and `DelayEvent.__init__`.** Save every parameter as a field, the same way `Job.__init__` does.

```
1 B-52H open None
1 120 original plan
```

**Step 2: `Tracker.__init__`, `find_job`, `create_job`.** `create_job` builds a `Job` and a version-1 `Estimate`.

```
Created job 1 for B-52H, planned for 120 days
B-52H
None
```

**Step 3: `rows_for_job` and the four estimate methods.**

```
120
120
```

**Step 4: `set_categories` and `log_delay`.**

```
Job 1, day 20: discovered_work (+15 days) - Corrosion found on wing spar
135
Error: 'weather' is not a valid category. Use one of: ['discovered_work', 'parts', 'staffing', 'other']
```

**Step 5: `percent`, `close_job`, `get_delays_for_job`, `total_days_by_category`, and the four report methods.** Among the report lines, look for these:

```
Closed job 1 after 140 days
Slip:            15 days (12.5% over the original plan)
  On time measured against REVISED targets:  0 of 1
```

**Step 6: switch the case study over.** In `tinker_case_study.py`, make two changes:

1. Replace `import prototype as tracker` with `from maintenance_tracker import Tracker`.
2. Add `tracker = Tracker()` as the first line inside `run_case_study()`.

Every other line stays the same. Then run `python3 compare_outputs.py`. Keep fixing until it says **MATCH**.

**Step 7 (after MATCH): switch the Navy case study over too.** Make the same two changes at the top of `navy_case_study.py`. Its extra report, `print_estimate_comparison()`, also reads dictionaries, so change those lookups to fields:

- `job["status"]` → `job.status`
- `job["actual_days"]` → `job.actual_days`
- `job["job_id"]` → `job.job_id`
- `job['asset']` → `job.asset`
- `estimates[i]["target_days"]` → `estimates[i].target_days`

It also uses `tracker.percent(...)`. In Phase 2, `percent` is a plain function in `maintenance_tracker.py`, not a method, so import it too: `from maintenance_tracker import Tracker, percent`, then write `percent(...)` without `tracker.` in front. Run the file and check that the averages at the bottom still read 82.0%, 63.3%, and 30.0%.

(`print_estimate_comparison` already takes `tracker` as a parameter, and `run_case_study` passes it in. That's what lets it see the same `Tracker` object that `run_case_study` created, so you don't need to change that part.)

## Part 6: When something goes wrong

| Error message | What it usually means |
|---|---|
| `AttributeError: 'NoneType' object has no attribute 'asset'` | A method you called still has `pass` in it (so it returns `None`), or `find_job` didn't find the job. |
| `TypeError: Tracker.find_job() takes 1 positional argument but 2 were given` | You forgot `self` in the `def` line. |
| `NameError: name 'jobs' is not defined` | You wrote `jobs` instead of `self.jobs`. |
| `NameError: name 'find_job' is not defined` | Inside a method, you wrote `find_job(...)` instead of `self.find_job(...)`. |
| `TypeError: 'Job' object is not subscriptable` | You used `job["asset"]` instead of `job.asset`. |
| `AttributeError: 'Estimate' object has no attribute 'version'` | That class's `__init__` still has `pass`, or a field name is misspelled. |
| `ModuleNotFoundError: No module named 'maintenance_tracker'` | A typo in the import, or you're running Python from a different folder than the files. |

The last line of an error message says what went wrong. The lines above it show which line of your code it happened on.

## Check yourself

1. What does `__init__` do, and when does it run?
2. In `t.find_job(1)`, what is `self`?
3. Why does `Tracker.__init__` create the lists, instead of making them global like Phase 1?
4. What's the difference between `import prototype as tracker` and `from maintenance_tracker import Tracker`?
5. What does `estimate["target_days"]` become in Phase 2?

### Answers

1. It sets up a new object's starting fields. It runs automatically every time you build an object, like `Job(1, "B-52H")`.
2. `t` — the tracker object the method was called on.
3. So each `Tracker` has its own lists. Two scenarios loaded at the same time won't mix their jobs together.
4. The first loads the whole `prototype.py` file under the nickname `tracker`, and you use its functions as `tracker.something`. The second pulls in just the `Tracker` class, so you can write `Tracker()` directly.
5. `estimate.target_days`
