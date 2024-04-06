from setup_test import DatabaseTest

from expense_tracker.import_dates import ImportantDate
from expense_tracker.database import DbAccess

def test_important_date():
    test_db = DatabaseTest()
    db = DbAccess(test_db.db_path)
    adate = ImportantDate.load(db, name="test date")
    test_db.clean()