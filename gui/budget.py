import streamlit as st
import pandas as pd

from expense_tracker.database import DbAccess
from expense_tracker.budget import Budget

def budget(db: DbAccess):
    options = [
        "Invalidate",
        "Balance",
    ]
    selected_view = st.sidebar.radio(
        "Budget Tool",
        options=options,
    )
    if selected_view == options[0]:
        invalidate(db)
    elif selected_view == options[1]:
        balance(db)
    else:
        st.error(f"Unknown buget mode: {selected_view}")

def balance(db: DbAccess):
    st.write(pd.DataFrame([i.model_dump() for i in Budget.load(db)]))

def invalidate(db: DbAccess):
    budget_id_to_invalidate = st.number_input(
        "Budget to Invalidate",
        min_value=0,
        step=1,
    )
    budget = Budget.load_single(db, budget_id_to_invalidate)
    st.write(budget.model_dump())
    if st.button("Invalidate"):
        st.success(f"Invalidating Budget {budget.name} ({budget.id})")
        db.update_value(budget, "valid", False)