from datetime import date

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from expense_tracker.database import DbAccess
from expense_tracker.category import Category, DbCategory
from expense_tracker.sub import DbSub, Sub
from expense_tracker.common import ZERO
from expense_tracker.execute import change_sub_budget

from helper_ui import select_category

def category(db: DbAccess):
    options = [
        "Data Check",
        "Invalidate",
        "View",
        "Analyze",
        "Switch Sub",
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
    elif selected_mode == options[4]:
        switch_sub_category(db)
    else:
        st.error(f"Unknown category mode: {selected_mode}")

def switch_sub_category(db: DbAccess):
    st.markdown("### Switch Sub Category")
    sub_id = st.number_input("Sub ID", step=1)
    selected_sub = None
    if sub_id != 0:
        selected_sub = Sub.upgrade_list(db, [DbSub.load_single(db, sub_id)])[0]
        st.write(selected_sub)
    new_category = select_category(db)
    if st.button("Switch Category"):
        if selected_sub is not None:
            change_sub_budget(db, selected_sub, new_category)
            st.success("Budget changed!")
        else:
            st.error("Selected sub is not assigned!")

def analyze(db: DbAccess):
    st.markdown("### Analyze")
    category_to_analyze = select_category(db)
    with st.expander("Category Details"):
        st.write(category_to_analyze.model_dump())
    if st.checkbox("Analyze Daily"):
        left, right = st.columns(2)
        start = left.date_input("Start Date")
        end = right.date_input("End Date")
        df = pd.DataFrame([s.model_dump() for s in DbSub.load(db, less_equal_date=end, greater_equal_date=start, category_id=category_to_analyze.id)])
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values(by="date")
        #st.write(df)
        rolling_average = st.checkbox("Add Rolling Average")
        if rolling_average:
            rolling_average_window = st.number_input("Rolling Average Window", min_value=1, step=1)
        plot_data = [
            go.Scatter(x=df["date"], y=df["amount"])
        ]
        if rolling_average:
                df["rolling_average_amount"] = df["amount"].rolling(rolling_average_window).mean()
                plot_data.append(go.Scatter(x=df["date"], y=df["rolling_average_amount"], line=dict(color='orange', width=1)))
        st.plotly_chart(go.Figure(
            data=plot_data,
        ))
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
        rolling_average = st.checkbox("Add Rolling Average")
        if rolling_average:
            rolling_average_window = st.number_input("Rolling Average Window", min_value=1, step=1)
        if st.button("Analyze"):
            df = pd.DataFrame([s.model_dump() for s in DbSub.load(db, less_than_date=end, greater_equal_date=start, category_id=category_to_analyze.id)])
            df["date"] = pd.to_datetime(df["date"])
            if remove_deposits:
                df = df.loc[df["amount"] < ZERO, :]
            df["year"] = df["date"].dt.year
            df["month"] = df["date"].dt.month
            df["month_label"] = df["year"].astype(str) + "-" + df["month"].astype(str)
            group_month = df[["amount", "month_label"]].groupby(by="month_label").sum().reset_index(drop=False)
            group_month["date"] = pd.to_datetime(group_month["month_label"])
            group_month = group_month.sort_values(by="date")
            st.markdown(f"{len(group_month)} Months")
            st.markdown(f"Monthly Average: `${group_month['amount'].mean()}`")
            st.markdown(f"Average Expense: `${df['amount'].mean()}`")
            st.markdown(f"Budget {category_to_analyze.budget.name} has increment ${category_to_analyze.budget.increment} with frequency {category_to_analyze.budget.frequency}")
            plot_data = [
                go.Bar(x=df["month_label"], y=df["amount"])
            ]
            if rolling_average:
                group_month["rolling_average_amount"] = group_month["amount"].rolling(rolling_average_window).mean()
                plot_data.append(go.Scatter(x=group_month["month_label"], y=group_month["rolling_average_amount"], line=dict(color='orange', width=1)))
            st.plotly_chart(go.Figure(
                data=plot_data,
            ))
            if show_data_table:
                st.write(df)
    if st.checkbox("Analyze Yearly"):
        start = date(
            st.number_input("Start Year", value=2023, step=1),
            1,
            1,
        )
        end = date(
            st.number_input("End Year", value=2024, step=1),
            12,
            31,
        )
        remove_deposits = st.checkbox("Remove Deposits")
        if st.button("Analyze"):
            df = pd.DataFrame([s.model_dump() for s in DbSub.load(db, less_equal_date=end, greater_equal_date=start, category_id=category_to_analyze.id)])
            df["date"] = pd.to_datetime(df["date"])
            if remove_deposits:
                df = df.loc[df["amount"] < ZERO, :]
            df["year"] = df["date"].dt.year
            plot_data = [
                go.Bar(x=df["year"], y=df["amount"])
            ]
            st.plotly_chart(go.Figure(
                data=plot_data,
            ))
            

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