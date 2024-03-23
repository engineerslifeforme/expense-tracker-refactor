from decimal import Decimal

import streamlit as st

from expense_tracker.database import DbAccess
from expense_tracker.transaction import Transaction
from expense_tracker.sub import Sub

from helper_ui import (
    taction_table,
    amount_input,
    sub_table,
    select_category,
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
    amount = amount_input(allow_negative=True)
    filter_category = st.checkbox("Filter Category")
    if filter_category:
        category_name = select_category(db).name
    if st.button("Search"):
        matches = sub_table(Sub.load(db, amount=amount))
        if filter_category:
            matches = matches.loc[matches["category"] == category_name, :]        
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
    amount = amount_input(allow_negative=True)
    if st.button("Search"):
        matches = Transaction.load(db, amount=amount)
        if len(matches) > 0:
            st.write(taction_table(matches))
        else:
            st.error("No Matches!")

