from expense_tracker.database import DbAccess
from expense_tracker.budget import Budget

def test_refresh():
    db = DbAccess("example.db")
    bud = Budget.load_single(db, 1)
    print("finished")