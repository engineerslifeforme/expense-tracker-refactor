import streamlit as st

from expense_tracker.database import DbAccess
from expense_tracker.budget import Budget

def budget(db: DbAccess):
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