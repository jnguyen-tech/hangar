# accounts.py
# Phase 6: user accounts and roles for the maintenance delay tracker.

import csv
import hashlib
import hmac
import os

# The website's accounts are saved here: usernames, roles, and password HASHES.
# Never the passwords themselves. This file is in .gitignore, so it stays off GitHub.
PROJECT_FOLDER = os.path.dirname(os.path.abspath(__file__))
USERS_FILE = os.path.join(PROJECT_FOLDER, "users.csv")

ROLES = ["employee", "manager", "admin"]
MINIMUM_PASSWORD_LENGTH = 8


# What each role is allowed to do.
# No role has "edit_history" or "delete_history", so nobody can rewrite the record.
PERMISSIONS = {
    "employee": ["view_jobs", "log_delay"],
    "manager": ["view_jobs", "log_delay", "open_job", "close_job", "view_reports"],
    "admin": ["view_jobs", "view_reports", "manage_accounts", "set_categories"],
}


def hash_password(password, salt):
    """Scramble a password so the original can't be read back.

    The same password and salt always give the same result.
    """
    scrambled = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100000)
    return scrambled.hex()

def can(user, action):
    """Return True if this user is allowed to do this action, or False if not."""
    if user is None:
        return False

    if not user.active:
        return False

    return action in PERMISSIONS[user.role]

class User:
    """One person who can log in."""

    def __init__(self, username, role, password_hash, salt):
        self.username = username
        self.role = role
        self.password_hash = password_hash
        self.salt = salt
        self.active = True


class Accounts:
    """Holds every user account, plus the methods that work on them."""

    def __init__(self):
        self.users = {}   # username -> that User

    def find_user(self, username):
        """Return the User with this username, or None."""
        if username in self.users:
            return self.users[username]
        return None

    def create_user(self, username, role, password):
        """Add a new account, after checking the username, the role, and the password.

        Returns an error message if something is wrong, or None if it worked.
        """
        if username == "":
            message = "Error: username can't be blank"
            print(message)
            return message

        if self.find_user(username) is not None:
            message = f"Error: user {username} already exists"
            print(message)
            return message

        if role not in ROLES:
            message = f"Error: '{role}' is not a valid role. Use one of: {ROLES}"
            print(message)
            return message

        if len(password) < MINIMUM_PASSWORD_LENGTH:
            message = f"Error: password must be at least {MINIMUM_PASSWORD_LENGTH} characters"
            print(message)
            return message

        salt = os.urandom(16)
        password_hash = hash_password(password, salt)
        self.users[username] = User(username, role, password_hash, salt)
        print(f"Created {role} account: {username}")


    def login(self, username, password):
        """Return the User if the username and password are right, or None if not."""
        user = self.find_user(username)
        if user is None:
            return None

        if not user.active:
            return None

        if not hmac.compare_digest(hash_password(password, user.salt), user.password_hash):
            return None

        return user

    def deactivate_user(self, username):
        """Turn an account off. It's kept, not deleted, so old records still show who made them."""
        user = self.find_user(username)
        if user is None:
            print(f"Error: user {username} not found")
            return

        user.active = False
        print(f"Deactivated account: {username}")

def save_accounts(accounts, filename):
    """Write every account to a CSV file, one row per user.

    The salt is bytes, so .hex() turns it into text that fits in a CSV.
    """
    file = open(filename, "w", newline="", encoding="utf-8")
    writer = csv.writer(file)
    writer.writerow(["username", "role", "salt", "password_hash", "active"])
    for user in accounts.users.values():
        writer.writerow([user.username, user.role, user.salt.hex(), user.password_hash, user.active])
    file.close()


def load_accounts(filename):
    """Read the accounts back from the CSV file. No file yet means no accounts yet."""
    accounts = Accounts()
    if not os.path.exists(filename):
        return accounts

    file = open(filename, encoding="utf-8")
    for row in csv.DictReader(file):
        # bytes.fromhex() turns the salt text back into bytes.
        user = User(row["username"], row["role"], row["password_hash"], bytes.fromhex(row["salt"]))
        user.active = (row["active"] == "True")
        accounts.users[user.username] = user
    file.close()
    return accounts


if __name__ == "__main__":
    # Step 1 test: create accounts and look them up.
    accounts = Accounts()
    accounts.create_user("admin1", "admin", "wrench-and-rivet")
    accounts.create_user("manager1", "manager", "hangar-door-7")
    accounts.create_user("employee1", "employee", "torque-spec-22")
    accounts.create_user("employee1", "employee", "torque-spec-22")   # rejected: already exists
    accounts.create_user("employee2", "supervisor", "torque-spec-22") # rejected: not a real role
    print(accounts.find_user("manager1").role)        # should print manager
    print(accounts.find_user("nobody"))               # should print None
    print("Accounts:", len(accounts.users))           # should print 3
    print()

    # Step 2 test: passwords are stored scrambled, never as plain text.
    accounts.create_user("employee3", "employee", "short")            # rejected: too short
    accounts.create_user("employee4", "employee", "torque-spec-22")   # same password as employee1
    user1 = accounts.find_user("employee1")
    user4 = accounts.find_user("employee4")
    print("Stored for employee1:", user1.password_hash[:20] + "...")
    print("Is the real password stored anywhere?", "torque-spec-22" in user1.password_hash)
    print("Same password, same stored value?", user1.password_hash == user4.password_hash)
    print()

    # Step 3 test: logging in.
    user = accounts.login("manager1", "hangar-door-7")
    print("Right password:", user.username, "logged in as", user.role)
    print("Wrong password:", accounts.login("manager1", "hangar-door-8"))
    print("Unknown user:", accounts.login("nobody", "hangar-door-7"))
    accounts.deactivate_user("employee4")
    print("Login after deactivating:", accounts.login("employee4", "torque-spec-22"))
    print()

    # Step 4 test: what each role is allowed to do.
    admin = accounts.login("admin1", "wrench-and-rivet")
    manager = accounts.login("manager1", "hangar-door-7")
    employee = accounts.login("employee1", "torque-spec-22")
    for action in ["view_jobs", "log_delay", "close_job", "view_reports", "manage_accounts", "edit_history"]:
        print(f"{action}: employee={can(employee, action)}, manager={can(manager, action)}, admin={can(admin, action)}")
    print("Not logged in:", can(None, "view_jobs"))