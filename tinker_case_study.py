# tinker_case_study.py
#
# Case study: depot maintenance delays at Oklahoma City Air Logistics Complex
# (Tinker AFB), based on the problems described in GAO report GAO-26-107890
# (May 2026).
#
# This file doesn't contain any tracking logic. It uses the general tool in
# prototype.py and supplies the Tinker-specific pieces:
#   * delay categories that match the causes GAO discusses
#   * the kinds of aircraft that go through depot maintenance at Tinker
#   * a sample set of jobs and delays
#
# ALL JOB DATA BELOW IS SYNTHETIC. The aircraft types are real, but every
# job, day count, and delay is made up to illustrate the problem. None of it
# is real Air Force data.
#
# Run it with:  python3 tinker_case_study.py
from maintenance_tracker import Tracker


# ---------------------------------------------------------------------------
# Scenario setup
# ---------------------------------------------------------------------------

# GAO highlights unplanned work discovered mid-maintenance, parts shortages,
# and workforce/staffing challenges as drivers of depot delays.
TINKER_CATEGORIES = ["discovered_work", "parts", "staffing", "other"]


def run_case_study():
    """Load the Tinker scenario into the tracker and print the reports."""
    tracker = Tracker()
    print("CASE STUDY: Depot maintenance delays, Oklahoma City ALC (Tinker AFB)")
    print("Synthetic data modeled on the problems described in GAO-26-107890\n")

    tracker.set_categories(TINKER_CATEGORIES)

    print("--- Opening jobs ---")
    tracker.create_job(1, "B-52H", 120)
    tracker.create_job(2, "B-1B", 90)
    tracker.create_job(3, "KC-135", 100)

    print("\n--- Logging delays ---")
    tracker.log_delay(1, 20, "discovered_work", "Corrosion found on wing spar", 15)
    tracker.log_delay(1, 45, "parts", "Waiting on replacement actuator", 10)
    tracker.log_delay(2, 30, "discovered_work", "Cracked bulkhead found during inspection", 20)
    tracker.log_delay(2, 50, "staffing", "Sheet metal crew shortage", 5)
    tracker.log_delay(3, 10, "bad_category", "This one should be rejected", 3)  # shows the error check

    print("\n--- Closing jobs ---")
    tracker.close_job(1, 145)
    tracker.close_job(2, 118)
    tracker.close_job(3, 98)

    for job_id in [1, 2, 3]:
        tracker.print_job_report(job_id)
    tracker.print_summary_report()


if __name__ == "__main__":
    run_case_study()
