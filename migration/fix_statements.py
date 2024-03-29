import sys
from pathlib import Path

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
    print("failed to fix statement transactions")