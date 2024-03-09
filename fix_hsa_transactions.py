import sys
from pathlib import Path

import pandas as pd
from tqdm import tqdm

from expense_tracker.database import DbAccess

db_path = Path(sys.argv[1])
assert(db_path.exists())

print(f"Fixing {db_path}")
db = DbAccess(db_path)

for hsa_transactions in tqdm(pd.read_sql_query("SELECT * FROM hsa_transactions", db.con).to_dict(orient="records")):
    if len(hsa_transactions["date"]) > 10:
        sql = f"UPDATE hsa_transactions SET date=\"{hsa_transactions['date'][0:10]}\" WHERE id={hsa_transactions['id']}"
        db.con.execute(sql)
        db.con.commit()