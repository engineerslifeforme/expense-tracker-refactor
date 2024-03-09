from expense_tracker.database import DbAccess
from expense_tracker.hsa_transactions import HsaTransaction
from expense_tracker.transaction import DbTransaction

db = DbAccess("example.db")
#HsaTransaction.load(db)
#DbTransaction.load_single(db, 11026)
DbTransaction.load(db)
print("complete")