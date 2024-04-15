from datetime import date
from decimal import Decimal

from expense_tracker.database import DbAccess
from expense_tracker.account import Account
from expense_tracker.method import Method
from expense_tracker.transaction import Transaction
from expense_tracker.sub import Sub
from expense_tracker.statement import DbStatement
from expense_tracker.hsa_transactions import DbHsaTransaction
from expense_tracker.budget import Budget
from expense_tracker.common import ZERO, NEGATIVE_ONE

def execute_transfer(
    db: DbAccess,
    taction_date: date,
    description: str,
    receipt: bool,
    withdrawal_account: Account,
    deposit_account: Account,
    method: Method,
    sub_contents: list,
):
    taction, subs = execute_transaction(
        db,
        taction_date,
        True,
        description,
        receipt,
        deposit_account,
        method,
        sub_contents,
    )
    new_content = []
    for amount, category in sub_contents:
        new_content.append(((NEGATIVE_ONE * amount).quantize(ZERO), category))
    w_taction, w_subs = execute_transaction(
        db,
        taction_date,
        True,
        description,
        receipt,
        withdrawal_account,
        method,
        new_content,
    )
    subs.extend(w_subs)
    return [taction, w_taction], subs

def execute_transaction(
    db: DbAccess,
    taction_date: date,
    transfer: bool,
    description: str,
    receipt: bool,
    account: Account,
    method: Method,
    sub_contents: list,
):
    next_taction_id = db.get_next_id(Transaction)
    taction = Transaction(
        id = next_taction_id,
        valid=True,
        date=taction_date,
        transfer=transfer,
        description=description,
        receipt=receipt,
        not_real=False,
        account=account,
        method=method,
        amount=ZERO,
    )
    taction.add_to_db(db)
    total_amount = ZERO
    subs = []
    for amount, category in sub_contents:
        next_sub_id = db.get_next_id(Sub)
        sub = Sub(
            id = next_sub_id,
            valid=True,
            amount=amount,
            not_real=False,
            category=category,
            taction=taction,
            date=taction_date,
        )
        sub.add_to_db(db)
        budget = Budget.load_single(db, sub.category.budget.id)
        budget.modify_balance(db, amount)
        next_taction_id += 1
        total_amount += amount
        subs.append(sub)
    account = Account.load_single(db, account.id)
    account.modify_balance(db, total_amount)
    db.update_value(taction, "amount", total_amount)
    return taction, subs

def invalidate_transaction(
    db: DbAccess,
    transaction_id: int
):
    transaction = Transaction.load_single(db, transaction_id)
    transaction.invalidate(db)
    transaction.account.add_to_balance(db, Decimal("-1") * transaction.amount)
    for sub in Sub.load(db, taction_id=transaction_id):
        sub.invalidate(db)
        sub.category.budget.add_to_balance(db, Decimal("-1") * sub.amount)
    for statement in DbStatement.load(db, taction_id=transaction_id):
        statement.unmap_taction(db)
    for hsa_transaction in DbHsaTransaction.load(db, expense_taction_id=transaction_id):
        hsa_transaction.unmap_expense_taction_id(db)
    for hsa_transaction in DbHsaTransaction.load(db, distribution_taction_id=transaction_id):
        hsa_transaction.unmap_distribution_taction_id(db)

