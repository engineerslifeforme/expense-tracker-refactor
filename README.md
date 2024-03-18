# Expense Tracker

A streamlit app that tracks expenses in a SQLite database.

I inherited the database format from a previous project so the project
does not currently have a way to setup a fresh database.  I may
attempt to fix that.

## TODO

1. Enter Transaction
2. Search
3. Delete

## Database

### Tables

1. account
2. sub
3. taction
4. method
5. category
6. budget
7. statement_transactions

#### taction

- `id`:
- `date`:
- `transfer`:
- `account_id`:
- `method_id`:
- `description`:
- `receipt`:
- `valid`:
- `not_real`:
