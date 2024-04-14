from datetime import date

import streamlit as st
import pandas as pd
from stqdm import stqdm

from expense_tracker.database import DbAccess
from expense_tracker.budget import Budget
from expense_tracker.import_dates import ImportantDate
from expense_tracker.budget_adjustments import DbBudgetAdjustment
from expense_tracker.account import Account
from expense_tracker.common import ZERO, NEGATIVE_ONE

from helper_ui import select_budget, amount_input

def budget(db: DbAccess):
    options = [
        "Invalidate",
        "Balance",
        "Update",
        "Invisible",
        "Budget to Account",
        "Budget Transfer",
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
    elif selected_view == options[5]:
        budget_transfer(db)
    else:
        st.error(f"Unknown buget mode: {selected_view}")

def budget_transfer(db: DbAccess):
    st.markdown("### Budget Transfer")
    left, right = st.columns(2)
    withdraw_budget = select_budget(
        db,
        label_prefix="Withdrawal",
        st_container=left,
    )
    right.markdown(f"Balance: ${withdraw_budget.balance}")
    left, right = st.columns(2)
    deposit_budget = select_budget(
        db,
        label_prefix="Deposit",
        st_container=left,
    )
    right.markdown(f"Balance: ${deposit_budget.balance}")
    amount = amount_input()
    st.markdown(f"Budget {withdraw_budget.name} new balance: ${withdraw_budget.balance - amount}")
    st.markdown(f"Budget {deposit_budget.name} new balance: ${deposit_budget.balance + amount}")
    if st.button("Transfer"):
        today = date.today()
        st.success("Transfer")
        DbBudgetAdjustment(
            amount=amount,
            date=today,
            valid=True,
            id=db.get_next_id(DbBudgetAdjustment),
            transfer=True,
            periodic_update=False,
            budget_id=deposit_budget.id,
        ).add_to_db(db)
        deposit_budget.add_to_balance(db, amount)
        negative_amount = amount * NEGATIVE_ONE
        DbBudgetAdjustment(
            amount=negative_amount,
            date=today,
            valid=True,
            id=db.get_next_id(DbBudgetAdjustment),
            transfer=True,
            periodic_update=False,
            budget_id=withdraw_budget.id,
        ).add_to_db(db)
        withdraw_budget.add_to_balance(db, negative_amount)
        withdraw_budget = Budget.load_single(db, withdraw_budget.id)
        deposit_budget = Budget.load_single(db, deposit_budget.id)
        st.markdown(f"New {withdraw_budget.name} balance: ${withdraw_budget.balance}")
        st.markdown(f"New {deposit_budget.name} balance: ${deposit_budget.balance}")

def budget_to_account(db: DbAccess):
    st.markdown("### Budget to Account Comparison")
    total_account_balance = sum([a.balance for a in Account.load(db)])
    st.markdown(f"Total Account Balance: ${total_account_balance}")
    visible_filter = None
    if st.checkbox("Filter to Only Visible", value=True):
        visible_filter = True
    budgets = Budget.load(db, visibility=visible_filter)
    positive_balance_total = sum([b.balance for b in budgets if b.balance > ZERO])
    st.markdown(f"Total Positive Budget Balance: ${positive_balance_total}")
    negative_balance_total = sum([b.balance for b in budgets if b.balance < ZERO])
    st.markdown(f"Total Negative Budget Balance: ${negative_balance_total}")
    net_budget_total = positive_balance_total + negative_balance_total
    st.markdown(f"Net Budget Balance ${net_budget_total}")
    st.markdown(f"Extra account headroom: ${net_budget_total}")

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