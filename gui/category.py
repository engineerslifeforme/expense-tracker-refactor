from datetime import date

import streamlit as st
import pandas as pd
import plotly.express as px

from expense_tracker.database import DbAccess
from expense_tracker.category import Category, DbCategory
from expense_tracker.sub import DbSub
from expense_tracker.common import ZERO

from helper_ui import select_category

def category(db: DbAccess):
    options = [
        "Data Check",
        "Invalidate",
        "View",
        "Analyze",
    ]
    selected_mode = st.sidebar.radio(
        "Category Mode",
        options = options,
    )

    if selected_mode == options[0]:
        check(db)
    elif selected_mode == options[1]:
        invalidate(db)
    elif selected_mode == options[2]:
        view(db)
    elif selected_mode == options[3]:
        analyze(db)
    else:
        st.error(f"Unknown category mode: {selected_mode}")

def analyze(db: DbAccess):
    st.markdown("### Analyze")
    category_to_analyze = select_category(db)
    if st.checkbox("Analyze Monthly"):
        left, right = st.columns(2)
        start_month = left.number_input("Start Month", min_value=1, step=1, max_value=12)
        start_year = right.number_input("Start Year", step=1, value=date.today().year)
        start = date(start_year, start_month, 1)
        
        end_month = left.number_input("End Month", min_value=1, step=1, max_value=12) + 1
        end_year = right.number_input("End Year", step=1, value=date.today().year)
        if end_month > 12:
            end_year += 1
            end_month = 1
        end = date(end_year, end_month, 1)
        remove_deposits = st.checkbox("Remove Deposits")
        show_data_table = st.checkbox("Show Data Table")
        if st.button("Analyze"):
            df = pd.DataFrame([s.model_dump() for s in DbSub.load(db, less_than_date=end, greater_equal_date=start, category_id=category_to_analyze.id)])
            df["date"] = pd.to_datetime(df["date"])
            if remove_deposits:
                df = df.loc[df["amount"] > ZERO, :]
            df["year"] = df["date"].dt.year
            df["month"] = df["date"].dt.month
            df["month_label"] = df["year"].astype(str) + "-" + df["month"].astype(str)
            st.plotly_chart(px.bar(
                df,
                x="month_label",
                y="amount",
            ))
            if show_data_table:
                st.write(df)

def view(db:DbAccess):
    st.dataframe(pd.DataFrame([c.model_dump() for c in DbCategory.load(db)]))

def invalidate(db: DbAccess):
    category_id_to_invalidate = st.number_input(
        "Category to Invalidate",
        min_value=0,
        step=1,
    )
    category = Category.load_single(db, category_id_to_invalidate)
    st.write(category.model_dump())
    if st.button("Invalidate"):
        st.success(f"Invalidating Category {category.name} ({category.id})")
        db.update_value(category, "valid", False)

def check(db: DbAccess):
    st.markdown("#### All budgets of valid categories are also valid?")
    errors_found = False
    for category in Category.load(db, valid=None):
        if category.valid and not category.budget.valid:
            st.error(f"Category {category.name} ({category.id}) is assigned to invalid budget {category.budget.name} ({category.budget.id})")
            errors_found = True
    if not errors_found:
        st.success("No valid categories found with invalid budgets")