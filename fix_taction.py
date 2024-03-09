import sys
from pathlib import Path

from tqdm import tqdm
import pandas as pd

from expense_tracker.transaction import DbTransaction
from expense_tracker.database import DbAccess
from expense_tracker.sub import Sub, DbSub
from expense_tracker.common import ZERO

db_path = Path(sys.argv[1])
assert(db_path.exists())

print(f"Fixing {db_path}")
db = DbAccess(db_path)

try:
    db.con.execute("ALTER TABLE taction ADD COLUMN `amount` decimal(10,2) DEFAULT NULL")
    db.con.commit()
except:
    # If column already created, this will fail
    pass
db.con.execute("UPDATE taction SET not_real=0 WHERE not_real IS NULL")
db.con.commit()
db.con.execute("UPDATE taction SET amount=0.00")
db.con.commit()

for taction in pd.read_sql_query("SELECT * FROM taction", db.con).to_dict(orient="records"):
    if len(taction["date"]) > 10:
        sql = f"UPDATE taction SET date=\"{taction['date'][0:10]}\" WHERE id={taction['id']}"
        db.con.execute(sql)
        db.con.commit()
        #print(sql)

#import pdb;pdb.set_trace()
tactions = DbTransaction.load(db)

for taction in tqdm(tactions):
    taction_subs = DbSub.load(db, taction_id=taction.id)
    total_amount = ZERO
    for sub in taction_subs:
        total_amount += sub.amount
    db.update_value(taction, "amount", total_amount)