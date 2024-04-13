import sys
from pathlib import Path

from tqdm import tqdm
import pandas as pd

from expense_tracker.database import DbAccess

db_path = Path(sys.argv[1])
assert(db_path.exists())

print(f"Fixing {db_path}")
db = DbAccess(db_path)

try:
    db.con.execute("ALTER TABLE statement_transactions ADD COLUMN `valid` tinyint(1) DEFAULT NULL")
    db.con.commit()
    db.con.execute("UPDATE statement_transactions SET valid=1")
    db.con.commit()
except:
    print("failed to add valid column to statement transactions, may already be present")

for statement in tqdm(pd.read_sql_query("SELECT * FROM statement_transactions", db.con).to_dict(orient="records")):
    if len(statement["date"]) > 10:
        sql = f"UPDATE statement_transactions SET date=\"{statement['date'][0:10]}\" WHERE id={statement['id']}"
        db.con.execute(sql)
        db.con.commit()