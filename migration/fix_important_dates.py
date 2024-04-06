import sys
from pathlib import Path

from expense_tracker.database import DbAccess

db_path = Path(sys.argv[1])
assert(db_path.exists())

print(f"Fixing {db_path}")
db = DbAccess(db_path)

modifications_need = False
try:
    db.con.execute("ALTER TABLE important_dates ADD COLUMN `valid` tinyint(1) DEFAULT NULL")
    db.con.commit()
    db.con.execute("UPDATE important_dates SET valid=1")
    db.con.commit()
    modifications_need = True
except:
    print("failed to fix important dates")

if modifications_need:
    db.con.execute("ALTER TABLE important_dates RENAME TO old_important_dates")
    db.con.execute("CREATE TABLE `important_dates` (`id` integer primary key AUTOINCREMENT, `name` text NOT NULL, `date` date NOT NULL, `valid` tinyint(1) DEFAULT NULL)")
    db.con.execute("INSERT INTO important_dates(name, date, valid) SELECT name, date, valid FROM old_important_dates")
    db.con.commit()