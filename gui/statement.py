from decimal import Decimal
from datetime import date

import streamlit as st
import pandas as pd

from expense_tracker.database import DbAccess

from helper_ui import select_account

def statement_scanning(db: DbAccess):
    options = [
        "Upload",
        "Assignment",
        "Check",
    ]
    mode = st.sidebar.radio(
        "Statement Mode",
        options=options,
    )
    if mode == options[0]:
        upload(db)
    elif mode == options[1]:
        pass
        # TODO: Assignment UI
    elif mode == options[2]:
        pass
        # TODO: Check UI
    else:
        st.error(f"Unknown mode: {mode}")

def upload(db: DbAccess):
    st.markdown("## Statement Scanning")
    uploaded_file = st.file_uploader("Choose a file")
    use_headers = "infer"
    if uploaded_file is not None:
        if st.checkbox("No CSV Header"):
            use_headers = None
        new_data = pd.DataFrame()
        dataframe = pd.read_csv(
            uploaded_file, 
            #parse_dates=["Expense Date"],
            dtype=str,
            header=use_headers,
        )
        st.write(dataframe)
        left, middle, right = st.columns(3)
        month = left.number_input(
            "Statement Month",
            min_value=1,
            step=1,
            max_value=12,
        )
        year = middle.number_input(
            "Statement Year",
            min_value=1950,
            step=1,
            max_value=2050,
            value=2024,
        )
        account_id = select_account(db, st_container=right).id
        left, middle, right = st.columns(3)
        date_column = left.selectbox(
            "Date Column",
            options=dataframe.columns
        )
        try:
            new_data["date"] = pd.to_datetime(dataframe[date_column]).dt.date
        except:
            middle.warning(f"Column `{date_column}` cannot be parsed as date")
        left, middle, right = st.columns(3)
        description_column = left.selectbox(
            "Description Column",
            options=dataframe.columns
        )
        new_data["description"] = dataframe[description_column]
        left, middle, right = st.columns(3)
        if left.checkbox("Split Credit/Debit"):
            credit_column = left.selectbox(
                "Credit Column",
                options=dataframe.columns
            )
            dataframe[credit_column] = dataframe[credit_column].fillna("0.00")
            try:
                dataframe["credit"] = dataframe[credit_column].apply(Decimal)
            except:
                middle.warning(f"Column `{credit_column}` cannot be converted to decimal")
            debit_column = left.selectbox(
                "Debit Column",
                options=dataframe.columns
            )
            dataframe[debit_column] = dataframe[debit_column].fillna("0.00")
            try:
                dataframe["debit"] = dataframe[debit_column].apply(Decimal)
            except:
                middle.warning(f"Column `{debit_column}` cannot be converted to decimal")
            try:
                new_data["amount"] = dataframe["credit"] - dataframe["debit"]
            except:
                pass
        else:
            amount_column = left.selectbox(
                "Amount Column",
                options=dataframe.columns
            )
            try:
                new_data["amount"] = dataframe[amount_column].apply(Decimal)
            except:
                middle.warning(f"Column `{amount_column}` cannot be converted to decimal")
        if st.checkbox("Flip Amount Sign"):
            new_data["amount"] = new_data["amount"] * Decimal("-1")
        st.write(new_data)
        if st.button("Add Unique Entries"):
            pass
            # TODO: Find entries that are not already present, then add to DB
    else:
        st.warning("Upload File")