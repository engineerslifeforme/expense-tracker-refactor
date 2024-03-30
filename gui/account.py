import streamlit as st
import pandas as pd

from expense_tracker.database import DbAccess
from expense_tracker.account import Account
from expense_tracker.transaction import DbTransaction
from expense_tracker.statement import DbStatement

from helper_ui import amount_input, taction_table, select_account

def account(db: DbAccess):
    options = [
        "Invalidate",
        "Balance",
        "Add",
    ]
    selected_view = st.sidebar.radio(
        "Account Tool",
        options=options,
    )
    if selected_view == options[0]:
        invalidate(db)
    elif selected_view == options[1]:
        balance(db)
    elif selected_view == options[2]:
        add(db)
    else:
        st.error(f"Unknown account mode: {selected_view}")

def add(db: DbAccess):
    st.markdown("## Add Account")
    name = st.text_input("Account Name")
    balance = amount_input(allow_negative=True, balance=True)
    purpose = st.selectbox(
        "Account Purpose",
        options=["Saving", "Spending"]
    )
    if st.button("Add Account"):
        next_id = db.get_next_id(Account)
        Account(
            id=next_id,
            name=name,
            visibility=True,
            purpose=purpose,
            valid=True,
            balance=balance
        ).add_to_db(db)
        st.success(f"Added {name}")

def balance(db: DbAccess):
    st.write(pd.DataFrame([i.model_dump() for i in Account.load(db)]))
    if st.checkbox("Check Transactions"):
        st.markdown("Recent Account Transactions")
        account_id = select_account(db).id
        transactions = pd.DataFrame([i.model_dump() for i in DbTransaction.load(db, account_id=account_id)])
        mapped_transactions = [s.taction_id for s in DbStatement.load(db)]
        transactions["mapped"] = transactions["id"].isin(mapped_transactions)
        st.write(transactions)
        st.markdown("#### Removed Unampped from balance")
        balance = Account.load_single(db, account_id).balance
        for transaction in transactions[~transactions["mapped"]].to_dict(orient="records"):
            if st.checkbox(f"Remove {transaction['id']} of ${transaction['amount']}"):
                balance -= transaction["amount"]
        st.markdown(f"New balance: ${balance}")
            


def invalidate(db: DbAccess):
    account_id_to_invalidate = st.number_input(
        "Account to Invalidate",
        min_value=0,
        step=1,
    )
    account = Account.load_single(db, account_id_to_invalidate)
    st.write(account.model_dump())
    if st.button("Invalidate"):
        st.success(f"Invalidating Account {account.name} ({account.id})")
        db.update_value(account, "valid", False)