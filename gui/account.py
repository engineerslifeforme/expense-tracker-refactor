import streamlit as st
import pandas as pd

from expense_tracker.database import DbAccess
from expense_tracker.account import Account

def account(db: DbAccess):
    options = [
        "Invalidate",
        "Balance",
    ]
    selected_view = st.sidebar.radio(
        "Account Tool",
        options=options,
    )
    if selected_view == options[0]:
        invalidate(db)
    elif selected_view == options[1]:
        balance(db)
    else:
        st.error(f"Unknown account mode: {selected_view}")

def balance(db: DbAccess):
    st.write(pd.DataFrame([i.model_dump() for i in Account.load(db)]))

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