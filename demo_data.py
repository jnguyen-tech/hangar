# demo_data.py
# Made-up sample jobs, so Hangar can be shown to anyone without the private dataset.
# Every job, number, and delay in this file is invented. None of it is real data.

import random
from maintenance_tracker import Tracker

CATEGORIES = ["discovered_work", "parts", "engineering_approval", "staffing", "other"]
ASSETS = ["B-52H", "B-1B", "KC-135"]

# Made-up descriptions for each cause of delay.
DESCRIPTIONS = {
    "discovered_work": [
        "Corrosion found on wing spar",
        "Cracked bulkhead found during inspection",
        "Wiring damage found behind a panel",
    ],
    "parts": [
        "Replacement actuator backordered",
        "Waiting on a landing gear part",
        "Wrong part shipped, reordered",
    ],
    "engineering_approval": [
        "Waiting on engineering approval for a repair",
        "Repair plan sent back for changes",
    ],
    "staffing": [
        "Sheet metal crew shortage",
        "Inspectors moved to another job",
    ],
    "other": [
        "Hangar space not available",
        "Tool calibration overdue",
    ],
}


def load_demo_tracker():
    """Build a Tracker filled with 200 made-up jobs."""
    random.seed(7)   # the same "random" jobs every time, so the demo never changes
    tracker = Tracker()
    tracker.quiet = True
    tracker.set_categories(CATEGORIES)

    # Job 1 is written out by hand, so there's always one clear example to show.
    tracker.create_job("DEMO-0001", "B-52H", 120)
    tracker.log_delay("DEMO-0001", 18, "discovered_work", "Corrosion found on wing spar", 15)
    tracker.log_delay("DEMO-0001", 40, "parts", "Replacement actuator backordered", 10)
    tracker.log_delay("DEMO-0001", 75, "engineering_approval", "Waiting on engineering approval for a repair", 12)
    tracker.close_job("DEMO-0001", 160)
    tracker.record_post_completion_revision("DEMO-0001", 160, 163)

    # Jobs 2 to 200 are made up with random numbers.
    for number in range(2, 201):
        job_id = f"DEMO-{number:04d}"
        planned_days = random.randint(90, 180)
        tracker.create_job(job_id, random.choice(ASSETS), planned_days)

        # Each job gets 0 to 4 delays.
        day = 0
        for i in range(random.randint(0, 4)):
            day += random.randint(5, 40)
            category = random.choice(CATEGORIES)
            description = random.choice(DESCRIPTIONS[category])
            tracker.log_delay(job_id, day, category, description, random.randint(3, 30))

        # The job finishes a little before or after its last target.
        last_target = tracker.get_current_estimate(job_id).target_days
        actual_days = last_target + random.randint(-15, 15)
        if actual_days <= day:
            actual_days = day + 1
        tracker.close_job(job_id, actual_days)

        # About 1 in 4 late jobs get their target moved AFTER they finished.
        if actual_days > last_target and random.randint(1, 4) == 1:
            tracker.record_post_completion_revision(job_id, actual_days, actual_days + random.randint(1, 10))

    return tracker


if __name__ == "__main__":
    tracker = load_demo_tracker()
    print("Demo jobs:", len(tracker.jobs))
    print("Demo delays:", len(tracker.delay_events))
    tracker.print_job_report("DEMO-0001")
    tracker.print_three_way_comparison()
