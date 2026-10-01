# navy_case_study.py
#
# Case study 2: maintenance delays for conventional Navy ships
# (destroyers and amphibious ships).
#
# Based on problems described in two public reports:
#   * Congressional Budget Office, "Maintenance Delays for Conventional Navy
#     Ships" (December 2025). CBO found that ship overhauls lasted 63% longer
#     than the Navy's first schedules on average, but only about 15% to 60%
#     longer than its final schedules -- so how late a ship looks depends on
#     which estimate you compare against. Overhauls with new or growth work
#     (work discovered once the ship is in the shipyard) took nearly 30%
#     longer than scheduled.
#   * GAO, "Navy Shipyards: Actions Needed to Address the Main Factors Causing
#     Maintenance Delays for Aircraft Carriers and Submarines" (GAO-20-588).
#     GAO found 38 of 51 maintenance periods finished late (fiscal years
#     2015-2019), with unplanned work contributing over 4,100 days of delay.
#
# Like tinker_case_study.py, this file has no tracking logic of its own. It
# uses the general tool in prototype.py and supplies the Navy-specific pieces.
#
# What's different about this scenario:
#   * The Navy makes several estimates BEFORE an overhaul starts: a class
#     plan, then a first schedule (about 2 years out), then a final schedule
#     (4-6 months out). Here, the class plan is version 1, and each later
#     schedule is logged as a "planning_revision" -- so it becomes its own
#     estimate version, and the history shows exactly when the plan moved.
#   * Day 0 is the day the overhaul starts. Negative days are before it starts
#     (day -730 is about two years before).
#   * An extra report at the bottom compares each ship's actual duration
#     against all three planning estimates -- the same comparison CBO made.
#
# ALL SHIP DATA BELOW IS SYNTHETIC. The ship types are real, but every
# overhaul, day count, and delay is made up to illustrate the problem.
#
# Run it with:  python3 navy_case_study.py

import prototype as tracker


# ---------------------------------------------------------------------------
# Scenario setup
# ---------------------------------------------------------------------------

# Causes of delay from the CBO and GAO reports, plus planning revisions.
NAVY_CATEGORIES = [
    "planning_revision",  # the plan was re-estimated before work started
    "growth_work",        # new or growth work found once the ship is in the yard
    "parts",              # parts and materials not available in time
    "workforce",          # shipyard workers not available
    "contracting",        # late contract awards that cut preparation time
    "other",
]

# The first three estimate versions for every ship, in order.
PLANNING_ESTIMATES = ["class plan", "first schedule", "final schedule"]


# ---------------------------------------------------------------------------
# Extra report for this case study
# ---------------------------------------------------------------------------

def print_estimate_comparison(tracker):
    """For each closed ship, compare its actual duration to each planning estimate.

    `tracker` is passed in as a parameter so this function uses the same
    tracker that run_case_study() filled with data.
    """
    print("\n=========== HOW LATE WAS EACH OVERHAUL? ===========")
    print("It depends on which estimate you compare against.")

    # One running total per planning estimate, used for the averages at the end.
    overrun_totals = [0, 0, 0]
    ship_count = 0

    for job in tracker.jobs:
        if job["status"] == "closed":
            ship_count += 1
            actual = job["actual_days"]
            estimates = tracker.get_estimates_for_job(job["job_id"])

            print(f"\n{job['asset']}: actually took {actual} days")
            # i = 0 is the class plan, 1 is the first schedule, 2 is the final schedule
            for i in range(len(PLANNING_ESTIMATES)):
                planned = estimates[i]["target_days"]
                overrun = tracker.percent(actual - planned, planned)
                overrun_totals[i] += overrun
                print(f"  vs {PLANNING_ESTIMATES[i]} ({planned} days): {overrun}% longer")

    print(f"\nAverage across all {ship_count} ships:")
    for i in range(len(PLANNING_ESTIMATES)):
        average = round(overrun_totals[i] / ship_count, 1)
        print(f"  vs {PLANNING_ESTIMATES[i]}: {average}% longer")


# ---------------------------------------------------------------------------
# Run the scenario
# ---------------------------------------------------------------------------

def run_case_study():
    """Load the Navy scenario into the tracker and print the reports."""
    print("CASE STUDY: Maintenance delays for conventional Navy ships")
    print("Synthetic data modeled on the problems described by CBO (Dec. 2025) and GAO-20-588\n")

    tracker.set_categories(NAVY_CATEGORIES)

    # The numbers below are chosen so the results land near CBO's averages:
    # about 63% longer than first schedules, and within CBO's 15%-60% range
    # against final schedules.

    print("--- Opening overhauls (version 1 = class plan) ---")
    tracker.create_job(1, "DDG-51 destroyer A", 150)
    tracker.create_job(2, "DDG-51 destroyer B", 150)
    tracker.create_job(3, "LSD amphibious ship", 180)

    print("\n--- Planning revisions before work starts ---")
    tracker.log_delay(1, -730, "planning_revision", "First schedule: ship older than the class plan assumed", 20)
    tracker.log_delay(1, -150, "planning_revision", "Final schedule: pre-overhaul inspections added repair items", 50)
    tracker.log_delay(2, -730, "planning_revision", "First schedule: ship older than the class plan assumed", 15)
    tracker.log_delay(2, -150, "planning_revision", "Final schedule: pre-overhaul inspections added repair items", 45)
    tracker.log_delay(3, -730, "planning_revision", "First schedule: work package grew", 20)
    tracker.log_delay(3, -150, "planning_revision", "Final schedule: pre-overhaul inspections added repair items", 40)

    print("\n--- Delays during the overhaul ---")
    tracker.log_delay(1, 40, "growth_work", "Hull corrosion found under deck plating", 50)
    tracker.log_delay(1, 90, "parts", "Replacement pump backordered", 15)
    tracker.log_delay(2, 35, "growth_work", "Structural cracking found in the mast", 45)
    tracker.log_delay(2, 120, "workforce", "Shipyard crew moved to another overhaul", 15)
    tracker.log_delay(3, 0, "contracting", "Contract awarded late, cutting preparation time", 20)
    tracker.log_delay(3, 60, "growth_work", "Piping corrosion found in the engine room", 45)

    print("\n--- Closing overhauls ---")
    tracker.close_job(1, 285)
    tracker.close_job(2, 280)
    tracker.close_job(3, 305)

    for job_id in [1, 2, 3]:
        tracker.print_job_report(job_id)
    tracker.print_summary_report()
    print_estimate_comparison(tracker)


if __name__ == "__main__":
    run_case_study()
