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

# Adding column to

```sql
ALTER TABLE taction ADD COLUMN `amount` decimal(10,2) DEFAULT NULL
```

```sql
ALTER TABLE hsa_transactions ADD COLUMN `valid` tinyint(1) DEFAULT NULL
```

This is slightly untested, but should be close.

```sql
ALTER TABLE hsa_transactions RENAME TO old_hsa_transactions
CREATE TABLE `hsa_transactions` (`id` integer primary key AUTOINCREMENT, "unique_identifier" text NOT NULL, `date` date, `amount` decimal(10,2), `expense_taction_id` int(11), `distribution_taction_id` int(11), `receipt_path` text, `eob_path` text, `bill_path` text, `valid` tinyint(1) DEFAULT NULL)
ALTER TABLE hsa_transactions RENAME COLUMN "id" TO "unique_identifier"
INSERT INTO hsa_transactions(unique_identifier, date, amount, expense_taction_id, distribution_taction_id, receipt_path, eob_path, bill_path, valid) SELECT id, date, amount, expense_taction_id, distribution_taction_id, receipt_path, eob_path, bill_path, valid FROM old_hsa_transactions;
```

```sql
ALTER TABLE hsa_receipt_paths RENAME TO old_paths;
CREATE TABLE IF NOT EXISTS "hsa_receipt_paths" (`id` integer primary key AUTOINCREMENT, `name` text NOT NULL, `path` text NOT NULL, `valid` tinyint(1) DEFAULT NULL);
INSERT INTO hsa_receipt_paths(name, path, valid) SELECT name, path, valid from old_paths
```