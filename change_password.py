# change_password.py
# Gives an existing Hangar login a new password. Run it from the project folder with:
#     python change_password.py
# Like add_user.py, the password is typed in secretly and only its hash is
# saved in users.csv. Run it on the computer (or PythonAnywhere) whose
# account you want to change, then restart or Reload the website.

from getpass import getpass
from accounts import USERS_FILE, load_accounts, save_accounts

accounts = load_accounts(USERS_FILE)
print("Accounts:", ", ".join(accounts.users))

username = input("Which username? ").strip()
password = getpass("New password (at least 8 characters, hidden as you type): ")
again = getpass("Type the new password again: ")

if password != again:
    print("The passwords don't match. Nothing was changed.")
else:
    error = accounts.change_password(username, password)
    if error is None:
        save_accounts(accounts, USERS_FILE)
        print("Saved. Restart the website (or click Reload on PythonAnywhere) to use it.")
