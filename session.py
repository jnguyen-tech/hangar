# session.py
# Phase 6: connects the login system to the tracker.
# A Session is one logged-in user working with the tracker.
# It checks permission before every action, then passes the request to the Tracker.

from accounts import Accounts, can
from maintenance_tracker import Tracker


class Session:
    """One logged-in user, plus the tracker they're working with."""

    def __init__(self, tracker, user):
        self.tracker = tracker
        self.user = user

    def allowed(self, action):
        """Return True if this session's user can do the action. If not, say so and return False."""
        if can(self.user, action):
            return True

        if self.user is None:
            print(f"Refused: you must log in to {action}")
        else:
            print(f"Refused: {self.user.username} ({self.user.role}) is not allowed to {action}")
        return False

    def create_job(self, job_id, asset, planned_days):
        if not self.allowed("open_job"):
            return
        self.tracker.create_job(job_id, asset, planned_days)

    def log_delay(self, job_id, logged_on_day, category, description, days_added):
        if not self.allowed("log_delay"):
            return
        self.tracker.log_delay(job_id, logged_on_day, category, description, days_added,
                               logged_by=self.user.username)

    def close_job(self, job_id, actual_days):
        if not self.allowed("close_job"):
            return
        self.tracker.close_job(job_id, actual_days)

    def set_categories(self, new_categories):
        if not self.allowed("set_categories"):
            return
        self.tracker.set_categories(new_categories)

    def print_job_report(self, job_id):
        if not self.allowed("view_jobs"):
            return
        self.tracker.print_job_report(job_id)
        self.tracker.print_delay_log(job_id)

    def print_summary_report(self):
        if not self.allowed("view_reports"):
            return
        self.tracker.print_summary_report()

    def create_user(self, accounts, username, role, password):
        if not self.allowed("manage_accounts"):
            return
        accounts.create_user(username, role, password)

    def deactivate_user(self, accounts, username):
        if not self.allowed("manage_accounts"):
            return
        if username == self.user.username:
            print("Error: you can't deactivate your own account")
            return
        accounts.deactivate_user(username)

if __name__ == "__main__":
    # Set up three accounts and one shared tracker.
    accounts = Accounts()
    accounts.create_user("admin1", "admin", "wrench-and-rivet")
    accounts.create_user("manager1", "manager", "hangar-door-7")
    accounts.create_user("employee1", "employee", "torque-spec-22")
    tracker = Tracker()
    print()

    # Each person logs in and gets their own session on the same tracker.
    admin = Session(tracker, accounts.login("admin1", "wrench-and-rivet"))
    manager = Session(tracker, accounts.login("manager1", "hangar-door-7"))
    employee = Session(tracker, accounts.login("employee1", "torque-spec-22"))
    stranger = Session(tracker, accounts.login("employee1", "wrong-password"))

    employee.create_job(1, "B-52H", 120)          # refused: employees can't open jobs
    manager.create_job(1, "B-52H", 120)           # allowed
    employee.log_delay(1, 20, "discovered_work", "Corrosion found on wing spar", 15)   # allowed
    manager.log_delay(1, 45, "parts", "Replacement fitting backordered", 10)           # allowed
    admin.log_delay(1, 50, "other", "Admin tries to log a delay", 5)                   # refused
    stranger.log_delay(1, 50, "other", "Not logged in", 5)                             # refused
    employee.close_job(1, 150)                    # refused: employees can't close jobs
    manager.close_job(1, 150)                     # allowed
    employee.print_summary_report()               # refused: employees can't view reports
    employee.print_job_report(1)                  # allowed
    print()

    # Step 6 test: only an admin can manage accounts.
    employee.create_user(accounts, "employee2", "manager", "sneaky-promotion")   # refused
    manager.deactivate_user(accounts, "employee1")                               # refused
    admin.create_user(accounts, "employee2", "employee", "rivet-gun-45")         # allowed
    admin.deactivate_user(accounts, "admin1")                                    # refused: own account
    admin.deactivate_user(accounts, "employee2")                                 # allowed
    print("Login after deactivating:", accounts.login("employee2", "rivet-gun-45"))