from decimal import Decimal

import streamlit as st

from expense_tracker.database import DbAccess
from expense_tracker.transaction import Transaction

from helper_ui import (
    taction_table,
    amount_input,
)

def search(db: DbAccess):
    st.markdown("### Search")

    search_modes = [
        "ID Search",
        "Data Search",
    ]

    search_mode = st.sidebar.radio(
        "Search Mode",
        options=search_modes
    )

    if search_mode == search_modes[0]:
        search_id(db)
    if search_mode == search_modes[1]:
        data_search(db)

def search_id(db: DbAccess):
    pass

def data_search(db: DbAccess):
    amount = amount_input(allow_negative=True)
    if st.button("Search"):
        matches = Transaction.load(db, amount=amount)
        if len(matches) > 0:
            st.write(taction_table(matches))
        else:
            st.error("No Matches!")

