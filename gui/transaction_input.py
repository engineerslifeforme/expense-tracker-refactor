import streamlit as st

from expense_tracker.database import DbAccess
from expense_tracker.account import Account
from expense_tracker.budget import Budget
from expense_tracker.execute import execute_transaction, execute_transfer
from expense_tracker.common import ZERO, ONE, NEGATIVE_ONE
from expense_tracker.transaction import Transaction
from helper_ui import (
    select_account,
    select_method,
    amount_input,
    select_category,
    taction_table,
)

def transaction_input(db: DbAccess):
    st.markdown("## Transaction Input")
    left, middle, right = st.columns(3)
    date = left.date_input("Date")
    receipt = middle.checkbox("Receipt")
    transfer = right.checkbox("Transfer")
    description = st.text_input("Description")
    left, middle, right = st.columns(3)
    if transfer:
        withdrawal_account = select_account(db, st_container=left, label_prefix="Withdrawal")
        deposit_account = select_account(db, st_container=middle, label_prefix="Deposit")
        method = select_method(db, st_container=right)            
        amount = amount_input(st_container=left)
        category = select_category(db, st_container=middle)
        sub_contents = [(amount, category)]
        total_amount = amount
    else:        
        withdraw = left.checkbox("Withdrawal", value=True)
        account = select_account(db, st_container=middle)
        method = select_method(db, st_container=right)            
        factor = ONE
        if withdraw:
            factor = NEGATIVE_ONE
        left, middle, right = st.columns(3)
        sub_count = left.number_input(
            "Quantity of Sub Transactions",
            min_value=1,
            step=1,
        )
        total_amount = ZERO
        sub_contents = []
        for i in range(1, sub_count+1):
            amount = (factor * amount_input(label_suffix=f"#{i}", st_container=middle)).quantize(ZERO)
            category = select_category(db, label_suffix=f"#{i}", st_container=right)
            sub_contents.append((amount, category))
            total_amount += amount
        st.write(f"Total Amount: ${total_amount}")
    if transfer:
        if st.button("Execute Transfer"):
            taction, subs = execute_transfer(
                db,
                date,
                description,
                receipt,
                withdrawal_account,
                deposit_account,
                method,
                sub_contents,
            )
    else:
        if st.button("Execute Transaction"):
            taction, subs = execute_transaction(
                db,
                date,
                transfer,
                description,
                receipt,
                account,
                method,
                sub_contents,
            )
            # TODO: Make this print for either transfer or simple transaction
            st.write(f"Created transaction id: {taction.id}")
            # Refreshing from database
            account = Account.load_single(db, account.id)
            st.write(f"New Account balance for {account.name} is ${account.balance}")
            for sub in subs:
                st.write(f"Created sub id: {sub.id}")
                # refresh from DB
                budget = Budget.load_single(db, sub.category.budget.id)
                st.write(f"Budget {budget.name} new balance: ${budget.balance}")
        st.markdown(f"Account balance: `${account.balance}` -> `${(account.balance + total_amount).quantize(ONE)}`")
        st.markdown("Budget changes:")
        for amount, category in sub_contents:
            balance = category.budget.balance
            st.markdown(f"(Category: {category.name}) Budget: {category.budget.name} `${balance}` -> `${(balance + amount).quantize(ONE)}`")        
    if total_amount != ZERO:
        matches = taction_table(
            Transaction.load(db, amount=total_amount)
        )
        if len(matches) > 0:
            st.markdown("### Matching Transactions")
            st.write(matches)