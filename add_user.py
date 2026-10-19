# add_user.py
# Makes a login for the Hangar website. Run it from the project folder with:
#     python add_user.py
# The password is typed in secretly (nothing shows on screen), and only its
# hash is saved, in users.csv. users.csv is in .gitignore, so it never goes
# to GitHub. Run this once on your computer and once on PythonAnywhere,
# since each one has its own users.csv.

from getpass import getpass
from accounts import ROLES, USERS_FILE, load_accounts, save_accounts

accounts = load_accounts(USERS_FILE)
print("Accounts so far:", len(accounts.users))

username = input("New username: ").strip()
role = input("Role (" + ", ".join(ROLES) + "): ").strip().lower()
password = getpass("Password (at least 8 characters, hidden as you type): ")
again = getpass("Type the password again: ")

if password != again:
    print("The passwords don't match. Nothing was saved.")
else:
    error = accounts.create_user(username, role, password)
    if error is None:
        save_accounts(accounts, USERS_FILE)
        print("Saved. You can log in on the website now (restart or Reload it first).")
