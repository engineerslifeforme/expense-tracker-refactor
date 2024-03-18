import sys
from pathlib import Path

import pandas as pd
from tqdm import tqdm

from expense_tracker.database import DbAccess

db_path = Path(sys.argv[1])
assert(db_path.exists())

print(f"Fixing {db_path}")
db = DbAccess(db_path)

transactions_need_modification = False
try:
    db.con.execute("ALTER TABLE hsa_transactions ADD COLUMN `valid` tinyint(1) DEFAULT NULL")
    db.con.commit()
    db.con.execute("UPDATE hsa_transactions SET valid=1")
    db.con.commit()
    transactions_need_modification = True
except:
    # If column already created, this will fail
    pass

paths_need_modification = False
try:
    db.con.execute("ALTER TABLE hsa_receipt_paths ADD COLUMN `valid` tinyint(1) DEFAULT NULL")
    db.con.commit()
    db.con.execute("UPDATE hsa_receipt_paths SET valid=1")
    db.con.commit()
    paths_need_modification = True
except:
    # If column already created, this will fail
    pass

if transactions_need_modification:
    db.con.execute("ALTER TABLE hsa_transactions RENAME TO old_hsa_transactions")
    db.con.execute("CREATE TABLE `hsa_transactions` (`id` integer primary key AUTOINCREMENT, \"unique_identifier\" text NOT NULL, `date` date, `amount` decimal(10,2), `expense_taction_id` int(11), `distribution_taction_id` int(11), `receipt_path` text, `eob_path` text, `bill_path` text, `valid` tinyint(1) DEFAULT NULL)")
    #db.con.execute("ALTER TABLE hsa_transactions RENAME COLUMN \"id\" TO \"unique_identifier\"")
    db.con.execute("INSERT INTO hsa_transactions(unique_identifier, date, amount, expense_taction_id, distribution_taction_id, receipt_path, eob_path, bill_path, valid) SELECT id, date, amount, expense_taction_id, distribution_taction_id, receipt_path, eob_path, bill_path, valid FROM old_hsa_transactions")
    db.con.commit()

if paths_need_modification:
    db.con.execute("ALTER TABLE hsa_receipt_paths RENAME TO old_paths")
    db.con.execute("CREATE TABLE IF NOT EXISTS \"hsa_receipt_paths\" (`id` integer primary key AUTOINCREMENT, `name` text NOT NULL, `path` text NOT NULL, `valid` tinyint(1) DEFAULT NULL)")
    db.con.execute("INSERT INTO hsa_receipt_paths(name, path, valid) SELECT name, path, valid from old_paths")

for hsa_transactions in tqdm(pd.read_sql_query("SELECT * FROM hsa_transactions", db.con).to_dict(orient="records")):
    if len(hsa_transactions["date"]) > 10:
        sql = f"UPDATE hsa_transactions SET date=\"{hsa_transactions['date'][0:10]}\" WHERE id={hsa_transactions['id']}"
        db.con.execute(sql)
        db.con.commit()