from decimal import Decimal

import streamlit as st
import pandas as pd

from expense_tracker.database import DbAccess
from expense_tracker.transaction import Transaction
from expense_tracker.sub import DbSub, Sub

from helper_ui import (
    taction_table,
    amount_input,
    sub_table,
    select_category,
    select_account,
)

def search(db: DbAccess):
    st.markdown("### Search")

    search_modes = [
        "Transaction ID Search",
        "Transaction Data Search",
        "Sub Data Search",
    ]

    search_mode = st.sidebar.radio(
        "Search Mode",
        options=search_modes
    )

    if search_mode == search_modes[0]:
        search_id(db)
    elif search_mode == search_modes[1]:
        transaction_data_search(db)
    elif search_mode == search_modes[2]:
        sub_data_search(db)

def sub_data_search(db: DbAccess):
    amount = None
    if st.checkbox("Filter by Amount"):
        amount = amount_input(allow_negative=True)
    category_id = None
    if st.checkbox("Filter Category"):
        category_id = select_category(db).id
    if st.button("Search"):
        matches = sub_table(Sub.upgrade_list(db, DbSub.load(db, amount=amount, category_id=category_id)))
        st.write(matches)

def search_id(db: DbAccess):
    st.write(taction_table([
        Transaction.load_single(
            db,
            st.number_input(
                "Transaction ID to Find",
                min_value=0,
                step=1,
            )
        )
    ]))

def transaction_data_search(db: DbAccess):
    amount = None
    left, right = st.columns(2)
    start = None
    end = None
    if left.checkbox("Filter by Date"):
        start = st.date_input("Start Date")
        end = st.date_input("End Date")
    if left.checkbox("Filter on Amount"):
        amount = amount_input(allow_negative=True, st_container=right)
    account_id = None
    if left.checkbox("Filter on Account"):
        account_id = select_account(db).id
    description = None
    left, right = st.columns(2)
    if left.checkbox("Filter Description"):
        right.info("Remember to use `%` as wildcard")
        description = right.text_input("Description Filter Content")
    
    if st.button("Search"):
        matches = Transaction.load(
            db, 
            amount=amount, 
            description=description, 
            less_equal_date=end, 
            greater_equal_date=start,
            account_id=account_id,
        )
        if len(matches) > 0:
            st.write(taction_table(matches))
        else:
            st.error("No Matches!")

