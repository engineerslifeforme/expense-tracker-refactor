from datetime import date
from decimal import Decimal

from expense_tracker.execute import execute_transaction
from expense_tracker.database import DbAccess
from expense_tracker.account import Account
from expense_tracker.method import Method
from expense_tracker.category import Category
from expense_tracker.transaction import DbTransaction
from expense_tracker.budget import Budget
from expense_tracker.sub import DbSub

from setup_test import DatabaseTest

def test_execute_transaction():
    test_db = DatabaseTest()
    db = DbAccess(test_db.db_path)
    account = Account.load(db)[0]
    method = Method.load(db)[0]
    category = Category.load(db)[0]
    budget = Budget.load(db)[0]
    
    # Check beginning state
    account_starting_balance = account.balance
    transaction_start_qty = len(DbTransaction.load(db))
    sub_start_qty = len(DbSub.load(db))
    budget_starting_balance = budget.balance
    
    amount = Decimal("1.00")
    execute_transaction(
        db,
        date(2024, 3, 1),
        False,
        "A transaction",
        True,
        account,
        method,
        [
            (amount, category)
        ]
    )

    # Check end state
    account = Account.load(db)[0]
    budget = Budget.load(db)[0]
    
    assert((account_starting_balance - amount) == account.balance)
    assert((budget_starting_balance - amount) == budget.balance)
    assert(transaction_start_qty + 1 == len(DbTransaction.load(db)))
    assert(sub_start_qty + 1 == len(DbSub.load(db)))
    
    print("complete")
    test_db.clean()