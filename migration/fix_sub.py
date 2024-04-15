import sys
from pathlib import Path

import pandas as pd
from tqdm import tqdm

from expense_tracker.database import DbAccess
from expense_tracker.transaction import DbTransaction

db_path = Path(sys.argv[1])
assert(db_path.exists())

print(f"Fixing {db_path}")
db = DbAccess(db_path)

df = pd.read_sql_query(
    "SELECT * FROM sub WHERE date IS NULL",
    db.con,
)

for sub in tqdm(df.to_dict(orient="records")):
    taction = DbTransaction.load_single(db, sub["taction_id"])
    db.con.execute(f"UPDATE sub SET date=\"{taction.date}\" WHERE id={sub['id']}")
    db.con.commit()