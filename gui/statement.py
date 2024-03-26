from decimal import Decimal
from datetime import date

import streamlit as st
import pandas as pd

from expense_tracker.database import DbAccess
from expense_tracker.statement import DbStatement
from expense_tracker.transaction import Transaction

from helper_ui import (
    select_account, 
    amount_input, 
    taction_table,
    select_category,
)

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
        assign(db)
    elif mode == options[2]:
        pass
        # TODO: Check UI
    else:
        st.error(f"Unknown mode: {mode}")

def assign(db: DbAccess):
    st.markdown("### Assign Statements to Transactions")
    unmapped = DbStatement.load(db, unmapped_taction=True)
    st.write(pd.DataFrame([i.model_dump() for i in unmapped]))
    quantity_to_show = st.number_input(
        "Quantity to View",
        value=20,
    )
    action_options = [
        "Nothing",
        "New",
        "Assign",
    ]
    for i in range(min([quantity_to_show, len(unmapped)])):
        index = i + 1
        active = unmapped[i]
        st.markdown(f"**Unmapped #{index}**")
        receipt = False
        left, middle, right = st.columns(3)
        category = select_category(
            db, 
            st_container=middle,
            label_suffix=f"# {index}"
        )
        date = right.date_input(
            f"Date #{index}",
            value=active.date,
        )
        transfer = False
        account_id = active.account_id
        amount = amount_input(
            label_suffix=f"#{index}",
            allow_negative=True,
            default=active.amount,
            st_container=left,
        )
        description = st.text_input(
            f"Description #{index}",
            value=active.description,
        )
        try:        
            st.write(taction_table(Transaction.load(db, amount=active.amount)).sort_values(by="date", ascending=False))
        except KeyError:
            st.warning(f"No matches on ${active.amount}")
        action = st.radio(f"Action #{index}", options=action_options)

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
        new_data["account_id"] = account_id
        new_data["statement_year"] = year
        new_data["statement_month"] = month
        st.write(new_data)
        #st.write(pd.DataFrame([i.model_dump() for i in DbStatement.load(db, valid=None)]))
        existing_data = pd.DataFrame([i.model_dump() for i in DbStatement.load(db, valid=None)])
        if st.button("Add Unique Entries"):
            skipped = 0
            for candidate_item in new_data.to_dict(orient="records"):
                duplicates = existing_data.loc[
                    (existing_data["date"] == candidate_item["date"]) &
                    (existing_data["account_id"] == candidate_item["account_id"]) &
                    (existing_data["amount"] == candidate_item["amount"]) &
                    (existing_data["description"] == candidate_item["description"])
                ]
                if len(duplicates) == 0:
                    new_id = db.get_next_id(DbStatement)
                    DbStatement(
                        id=new_id,
                        date=candidate_item["date"],
                        amount=candidate_item["amount"],
                        valid=True,
                        statement_month=candidate_item["statement_month"],
                        statement_year = candidate_item["statement_year"],
                        description=candidate_item["description"],
                        deferred = False,
                        account_id=candidate_item["account_id"],                        
                    ).add_to_db(db)
                    st.success(f"Added statement {new_id}")
                else:
                    skipped += 1
            st.markdown(f"Of {len(new_data)} items, skipped {skipped}")
    else:
        st.warning("Upload File")