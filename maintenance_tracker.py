# maintenance_tracker.py
#
# The maintenance delay tracker, written with classes.
#
# What changes from prototype.py:
#   * Dictionaries become objects:   job["asset"]   ->  job.asset
#   * Global lists become fields:    jobs           ->  self.jobs
#   * Functions become methods:      find_job(1)    ->  self.find_job(1)
#   * Methods always take `self` as their first parameter. `self` means
#     "this particular object," so each Tracker has its own lists.
#
# __init__ is the method Python runs automatically when you create an object,
# like Job(1, "B-52H"). Its job is to set up the object's starting fields.


def percent(part, whole):
    """Return part as a percentage of whole, rounded to 1 decimal place.

    Replaces: percent() in prototype.py. Copy it over unchanged --
    it doesn't need to be inside a class.
    """
    if whole == 0:
        return 0.0
    return round(part / whole * 100, 1)


# ===========================================================================
# The three record classes (these replace the dictionaries)
# ===========================================================================

class Job:
    """One maintenance job on one asset. Replaces the job dictionaries."""

    def __init__(self, job_id, asset):
        # EXAMPLE -- already filled in. Each parameter is saved as a field on
        # the object with `self.`, and fields that always start the same way
        # (status, actual_days) get their starting value here.
        self.job_id = job_id
        self.asset = asset
        self.status = "open"
        self.actual_days = None


class Estimate:
    """One version of a job's planned finish. Replaces the estimate dictionaries."""

    def __init__(self, job_id, version, target_days, created_on_day, reason, delay_event_id):
        self.job_id = job_id
        self.version = version
        self.target_days = target_days
        self.created_on_day = created_on_day
        self.reason = reason
        self.delay_event_id = delay_event_id
        self.after_completion = False


class DelayEvent:
    """One problem that pushed a job's finish out. Replaces the delay event dictionaries."""

    def __init__(self, event_id, job_id, category, description, logged_on_day, days_added):
        self.event_id = event_id
        self.job_id = job_id
        self.category = category
        self.description = description
        self.logged_on_day = logged_on_day
        self.days_added = days_added
        self.logged_by = None
# ===========================================================================
# The Tracker (replaces the global lists and all the functions)
# ===========================================================================

class Tracker:
    """Holds one scenario's jobs, estimates, delays, and categories, plus every method that works on them."""

    def __init__(self):
        #   self.categories -> ["discovered_work", "parts", "staffing", "other"]
        self.jobs = []
        self.estimates = []
        self.delay_events = []
        self.categories = ["discovered_work", "parts", "staffing", "other"]
        # Lookup dictionaries, so finding things stays fast with 50,000 jobs.
        self.job_lookup = {}         # job_id -> that Job
        self.estimates_by_job = {}   # job_id -> list of that job's Estimates
        self.delays_by_job = {}      # job_id -> list of that job's DelayEvents
        self.quiet = False           # True = skip the message for every job and delay

    # --- Categories ----------------------------------------------------------

    def set_categories(self, new_categories):
        """Replace the allowed delay categories.

        Replaces: set_categories() in prototype.py.
        """
        self.categories.clear()
        for category in new_categories:
            self.categories.append(category)

    # --- Helpers ---------------------------------------------------------------

    def rows_for_job(self, table, job_id):
        """Return every object in a list (self.estimates or self.delay_events) that belongs to job_id.

        Replaces: rows_for_job() in prototype.py.
        Hint: row["job_id"] becomes row.job_id
        """
        matches = []
        for row in table:
            if row.job_id == job_id:
                matches.append(row)
        return matches

    def total_days_by_category(self, events):
        """Add up days_added for each category and return a dictionary of totals.

        Replaces: total_days_by_category() in prototype.py.
        Hint: `totals` is still a dictionary. Only the events changed:
        event["category"] becomes event.category
        """
        totals = {}
        for category in self.categories:
            totals[category] = 0
        
        for event in events:
            totals[event.category] += event.days_added
        
        return totals

    # --- Jobs ------------------------------------------------------------------

    def find_job(self, job_id):
        """Return the Job with this id, or None."""
        if job_id in self.job_lookup:
            return self.job_lookup[job_id]
        return None

    def create_job(self, job_id, asset, planned_days):
        """Open a new job and record its ORIGINAL estimate as version 1.

        Replaces: create_job() in prototype.py.
        Hint: jobs.append({...}) becomes self.jobs.append(Job(job_id, asset))
        and the first estimate becomes an Estimate(...) object.
        """
        if self.find_job(job_id) is not None:
            print(f"Error: job {job_id} already exists")
            return

        job = Job(job_id, asset)
        estimate = Estimate(job_id, 1, planned_days, 0, "original plan", None)
        self.jobs.append(job)
        self.estimates.append(estimate)
        self.job_lookup[job_id] = job
        self.estimates_by_job[job_id] = [estimate]
        self.delays_by_job[job_id] = []

        if not self.quiet:
            print(f"Created job {job_id} for {asset}, planned for {planned_days} days")

    def close_job(self, job_id, actual_days):
        """Mark a job closed and record how long it actually took.

        Replaces: close_job() in prototype.py.
        """
        job = self.find_job(job_id)
        if job is None:
            print(f"Error: job {job_id} not found")
            return
        
        job.status = "closed"
        job.actual_days = actual_days
        if not self.quiet:
            print(f"Closed job {job_id} after {actual_days} days")

    # --- Estimates (append-only) ----------------------------------------------

    def get_estimates_for_job(self, job_id):
        """Every Estimate for a job, oldest first.

        Replaces: get_estimates_for_job() in prototype.py.
        """
        return self.estimates_by_job[job_id]

    def get_original_estimate(self, job_id):
        """The first Estimate for a job.

        Replaces: get_original_estimate() in prototype.py.
        """
        return self.get_estimates_for_job(job_id)[0] 

    def get_current_estimate(self, job_id):
        """The most recent Estimate for a job.

        Replaces: get_current_estimate() in prototype.py.
        """
        return self.get_estimates_for_job(job_id)[-1]

    def get_last_regular_estimate(self, job_id):
        """The most recent Estimate made BEFORE the job finished (skips post-completion revisions)."""
        last = None
        for estimate in self.get_estimates_for_job(job_id):
            if not estimate.after_completion:
                last = estimate
        return last

    def record_post_completion_revision(self, job_id, target_days, created_on_day):
        """Append a revision made AFTER the job finished. It's kept in the history, but marked."""
        current = self.get_current_estimate(job_id)
        estimate = Estimate(
            job_id,
            current.version + 1,
            target_days,
            created_on_day,
            "post-completion revision (no delay logged)",
            None,
        )
        estimate.after_completion = True
        self.estimates.append(estimate)
        self.estimates_by_job[job_id].append(estimate)
    
    def revise_estimate(self, job_id, delay_event):
        """Append a NEW Estimate based on a DelayEvent. Never change old ones."""
        current = self.get_current_estimate(job_id)
        new_estimate = Estimate(
            job_id,
            current.version + 1,
            current.target_days + delay_event.days_added,
            delay_event.logged_on_day,
            delay_event.description,
            delay_event.event_id,
        )
        self.estimates.append(new_estimate)
        self.estimates_by_job[job_id].append(new_estimate)
    # --- Delay events ------------------------------------------------------------

    def get_delays_for_job(self, job_id):
        """Every DelayEvent for a job, oldest first.

        Replaces: get_delays_for_job() in prototype.py.
        """
        return self.delays_by_job[job_id]

    def log_delay(self, job_id, logged_on_day, category, description, days_added, event_id=None, logged_by=None):
        """Check the job and category, save a DelayEvent, then revise the estimate."""
        if self.find_job(job_id) is None:
            print(f"Error: job {job_id} not found")
            return

        if category not in self.categories:
            print(f"Error: '{category}' is not a valid category. Use one of: {self.categories}")
            return

        if event_id is None:
            event_id = len(self.delay_events) + 1

        event = DelayEvent(
            event_id,
            job_id,
            category,
            description,
            logged_on_day,
            days_added,
        )
        event.logged_by = logged_by
        self.delay_events.append(event)
        self.delays_by_job[job_id].append(event)
        self.revise_estimate(job_id, event)

        if not self.quiet:
            print(f"Job {job_id}, day {logged_on_day}: {category} (+{days_added} days) - {description}")

    # --- Reports -----------------------------------------------------------------
    
    def print_delay_log(self, job_id):
        """Print every delay on a job, with who logged it."""
        if self.find_job(job_id) is None:
            print(f"Error: job {job_id} not found")
            return

        print(f"\nDelay log for job {job_id}:")
        for event in self.get_delays_for_job(job_id):
            print(f"  Day {event.logged_on_day}: {event.category} (+{event.days_added} days) - {event.description} [logged by {event.logged_by}]")
    def print_job_report(self, job_id):
        """Print one job's original vs. current target, history, and slip by cause.

        Replaces: print_job_report() in prototype.py.
        """
        job = self.find_job(job_id)
        if job is None:
            print(f"Error: job {job_id} not found")
            return
    
        original = self.get_original_estimate(job_id).target_days
        current = self.get_current_estimate(job_id).target_days
        slip = current - original
    
        print(f"\n=== Job {job_id}: {job.asset} ({job.status}) ===")
        print(f"Original target: {original} days")
        print(f"Current target:  {current} days")
        print(f"Slip:            {slip} days ({percent(slip, original)}% over the original plan)")
    
        print("Estimate history:")
        for estimate in self.get_estimates_for_job(job_id):
            print(f"  v{estimate.version}: {estimate.target_days} days - {estimate.reason}")
    
        print("Slip by cause:")
        delays = self.get_delays_for_job(job_id)
        if len(delays) == 0:
            print("  none - no delays logged")
        else:
            totals = self.total_days_by_category(delays)
            for category in self.categories:
                if totals[category] > 0:
                    print(f"  {category}: {totals[category]} days")
    
        if job.status == "closed":
            print(f"Actually finished in {job.actual_days} days")

    def print_slip_by_cause(self):
        """Print total slip across all jobs, split by cause.

        Replaces: print_slip_by_cause() in prototype.py.
        """
        totals = self.total_days_by_category(self.delay_events)
        
        total_slip = 0
        for category in self.categories:
            total_slip += totals[category]
    
        print(f"Total slip across all jobs: {total_slip} days")
        for category in self.categories:
            days = totals[category]
            print(f"  {category}: {days} days ({percent(days, total_slip)}%)")
        

    def print_on_time_comparison(self):
        """Print on-time counts against original vs. revised targets.

        Replaces: print_on_time_comparison() in prototype.py.
        """
        closed_jobs = []
        for job in self.jobs:
            if job.status == "closed":
                closed_jobs.append(job)
    
        on_time_vs_original = 0
        on_time_vs_revised = 0
        for job in closed_jobs:
            original = self.get_original_estimate(job.job_id).target_days
            revised = self.get_last_regular_estimate(job.job_id).target_days
            if job.actual_days <= original:
                on_time_vs_original += 1
            if job.actual_days <= revised:
                on_time_vs_revised += 1
    
        hidden = on_time_vs_revised - on_time_vs_original

        print(f"\nClosed jobs: {len(closed_jobs)}")
        print(f"  On time measured against REVISED targets:  {on_time_vs_revised} of {len(closed_jobs)}")
        print(f"  On time measured against ORIGINAL targets: {on_time_vs_original} of {len(closed_jobs)}")
        print(f"  Jobs that only look on time because the target moved: {hidden}")

    def print_three_way_comparison(self):
        """Print on-time counts against the original target, the last regular target,
        and the final record (after post-completion revisions)."""
        closed_jobs = 0
        vs_original = 0
        vs_regular = 0
        vs_final = 0
        for job in self.jobs:
            if job.status != "closed":
                continue
            closed_jobs += 1
            if job.actual_days <= self.get_original_estimate(job.job_id).target_days:
                vs_original += 1
            if job.actual_days <= self.get_last_regular_estimate(job.job_id).target_days:
                vs_regular += 1
            if job.actual_days <= self.get_current_estimate(job.job_id).target_days:
                vs_final += 1

        print(f"\nClosed jobs: {closed_jobs}")
        print(f"  On time vs ORIGINAL target:                     {vs_original} ({percent(vs_original, closed_jobs)}%)")
        print(f"  On time vs LAST target set before finishing:    {vs_regular} ({percent(vs_regular, closed_jobs)}%)")
        print(f"  On time vs FINAL record (after-the-fact edits): {vs_final} ({percent(vs_final, closed_jobs)}%)")
        print(f"  Made to look on time by revisions during the job: {vs_regular - vs_original}")
        print(f"  Made to look on time by revisions AFTER the job:  {vs_final - vs_regular}")
    
    def print_summary_report(self):
        """Print the summary header, then the two reports above.

        Replaces: print_summary_report() in prototype.py.
        """
        print("\n=========== SUMMARY: ALL JOBS ===========")
        self.print_slip_by_cause()
        self.print_on_time_comparison()
        


# ===========================================================================
# Test as you go
# ===========================================================================
# Run this file with:  python3 maintenance_tracker.py
# As you finish each step, remove the # from that step's test lines.

if __name__ == "__main__":
    print("maintenance_tracker.py self-test")

    # Step 1 -- Job, Estimate, and DelayEvent __init__ methods
    job = Job(1, "B-52H")
    print(job.job_id, job.asset, job.status, job.actual_days)
    est = Estimate(1, 1, 120, 0, "original plan", None)
    print(est.version, est.target_days, est.reason)
    print()

    # Step 2 -- Tracker.__init__, find_job, create_job
    t = Tracker()
    t.create_job(1, "B-52H", 120)
    print(t.find_job(1).asset)       # should print B-52H
    print(t.find_job(99))            # should print None
    print()

    # Step 3 -- estimate methods (needs rows_for_job too)
    print(t.get_original_estimate(1).target_days)   # should print 120
    print(t.get_current_estimate(1).target_days)    # should print 120
    print()

    # Step 4 -- set_categories and log_delay
    t.set_categories(["discovered_work", "parts", "staffing", "other"])
    t.log_delay(1, 20, "discovered_work", "Corrosion found on wing spar", 15)
    print(t.get_current_estimate(1).target_days)    # should print 135
    t.log_delay(1, 25, "weather", "Should be rejected", 2)
    print()

    # Step 5 -- percent, close_job, get_delays_for_job, total_days_by_category,
    #           and the four report methods
    t.close_job(1, 140)
    t.print_job_report(1)
    t.print_summary_report()
    print()

    # Step 6 -- switch tinker_case_study.py over to your classes. Two changes:
    #   1. Replace   import prototype as tracker
    #      with      from maintenance_tracker import Tracker
    #   2. Add       tracker = Tracker()
    #      as the first line inside run_case_study()
    # Every other line in the case study stays the same. Then run:
    #   python3 compare_outputs.py
