from datetime import date

import streamlit as st
import pandas as pd
from stqdm import stqdm

from expense_tracker.database import DbAccess
from expense_tracker.budget import Budget
from expense_tracker.import_dates import ImportantDate
from expense_tracker.budget_adjustments import DbBudgetAdjustment

from helper_ui import select_budget

def budget(db: DbAccess):
    options = [
        "Invalidate",
        "Balance",
        "Update",
        "Invisible",
        "Budget to Account",
    ]
    selected_view = st.sidebar.radio(
        "Budget Tool",
        options=options,
    )
    if selected_view == options[0]:
        invalidate(db)
    elif selected_view == options[1]:
        balance(db)
    elif selected_view == options[2]:
        update(db)
    elif selected_view == options[3]:
        invisible(db)
    elif selected_view == options[4]:
        budget_to_account(db)
    else:
        st.error(f"Unknown buget mode: {selected_view}")

def budget_to_account(db: DbAccess):
    st.markdown("### Budget to Account Comparison")
    

def invisible(db: DbAccess):
    budget = select_budget(db)
    st.write(budget.model_dump())
    if st.button("Invisible"):
        st.success(f"Setting visibility to `False` for Budget {budget.name} ({budget.id})")
        budget.set_invisible(db)

def update(db: DbAccess):
    st.markdown("### Update Budgets")
    last_update = ImportantDate.load(db, name="last_budget_update")[0]
    today = date.today()
    if last_update.date < date(today.year, today.month, 1):
        st.warning(f"Budgets need updating!  Last update: {last_update.date}")
        if st.button("Update Budgets!"):
            budgets = Budget.load(db)
            for budget in stqdm(budgets):
                increment_add = budget.monthly_increment_amount
                DbBudgetAdjustment(
                    amount=increment_add,
                    date=today,
                    valid=True,
                    id=db.get_next_id(DbBudgetAdjustment),
                    transfer=False,
                    periodic_update=True,
                    budget_id=budget.id,
                ).add_to_db(db)
                budget.monthly_increment_balance(db, today)
            st.success(f"{len(budgets)} Budgets Updated!")
            new_month = last_update.date.month + 1
            new_year = last_update.date.year
            if new_month > 12:
                new_month = 1
                new_year += 1
            new_update = date(new_year, new_month, 1)
            st.success(f"Budgets updated to {new_update}")
            last_update.change_date(db, new_update)
    else:
        st.success("All Budgets up to date!")

def balance(db: DbAccess):
    visibility_filter = None
    if st.checkbox("Filter Invisible", value=True):
        visibility_filter = True
    budgets = Budget.load(db, visibility=visibility_filter)
    st.write(pd.DataFrame([i.model_dump() for i in budgets]))

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