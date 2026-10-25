# Security Policy

Hangar is a student portfolio project. It isn't connected to any Air Force or other maintenance system, and the data it uses is synthetic.

## What's supported

Only the latest code on the `main` branch, and the live site at https://jnguyentech.pythonanywhere.com, get fixes.

## How it protects itself

- Passwords are never stored. Only a salted hash is kept, and the accounts file (`users.csv`) never goes to GitHub.
- After 5 wrong passwords in a row, an account is locked for 10 minutes.
- Every form checks the logged-in user's role on the server, not just in the page.
- Database queries use `?` placeholders, so typed text can't change the SQL.
- The history is append-only: database triggers refuse any edit or delete.

## Reporting a problem

If you find a security problem, please don't open a public issue. Email john.nguyen4@my.occc.edu with what you found and how to reproduce it. I'll reply within a week.
