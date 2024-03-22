from decimal import Decimal

import streamlit as st
import pandas as pd

from expense_tracker.database import DbAccess
from expense_tracker.hsa_transactions import DbHsaTransaction
from expense_tracker.transaction import Transaction
from expense_tracker.receipt_paths import ReceiptPath
from expense_tracker.common import NEGATIVE_ONE
from helper_ui import (
    taction_table, 
    list_to_df,
    select_category,
)

def hsa_management(db: DbAccess):
    hsa_tasks = [
        "Assignment",
        "Upload Records",
        "Find Expenses to Claim",
    ]
    hsa_task = st.sidebar.radio(
        "Current HSA Task",
        options=hsa_tasks
    )
    if hsa_task == hsa_tasks[0]:
        hsa_assignment(db)
    elif hsa_task == hsa_tasks[1]:
        upload_record(db)
    elif hsa_task == hsa_tasks[2]:
        find_expenses(db)
    else:
        st.error(f"Unknown HSA task: {hsa_task}")

def find_expenses(db: DbAccess):
    st.markdown("### Find Expenses to Claim")
    filter_category = select_category(db)
    if st.button("Show Expenses"):
        existing = DbHsaTransaction.load(db)


def upload_record(db: DbAccess):
    st.markdown("### Upload HSA Record")
    uploaded_file = st.file_uploader("Choose a file")
    if uploaded_file is not None:
        dataframe = pd.read_csv(
            uploaded_file, 
            parse_dates=["Expense Date"],
            dtype={'Submitted Amount': str},
        )
        dataframe['Submitted Amount'] = dataframe['Submitted Amount'].apply(Decimal)
        st.markdown(f"{len(dataframe)} Total Entries")
        dataframe = dataframe.loc[dataframe["Expense Description"] == "Distribution", :]
        st.markdown(f"{len(dataframe)} Total Distributions")
        dataframe = generate_unique_identifier(dataframe)
        db_records = list_to_df(DbHsaTransaction.load(db))
        dataframe = dataframe.loc[~dataframe["unique_identifier"].isin(db_records["unique_identifier"]), :]
        st.markdown(f"{len(dataframe)} Unrecorded Distributions")
        if st.checkbox("View Remaining Entries"):
            st.write(dataframe)
        if st.button("Add Entries"):
            for entry in dataframe.to_dict(orient="records"):
                new_id = db.get_next_id(DbHsaTransaction)
                DbHsaTransaction(
                    valid=True,
                    id=new_id,
                    unique_identifier=entry["unique_identifier"],
                    amount=entry["Submitted Amount"],
                    date=entry["Expense Date"],
                ).add_to_db(db)
                st.markdown(f"Added HSA Transaction ID: {new_id}")
    else:
        st.warning("Upload a file!")

def hsa_assignment(db: DbAccess):
    transactions = DbHsaTransaction.load(db)
    st.write(f"Total Transactions: {len(transactions)}")
    st.sidebar.markdown("Transaction Filters")
    if st.sidebar.checkbox("Only Unmapped Expense"):
        transactions = [t for t in transactions if t.expense_taction_id is None]
    if st.sidebar.checkbox("Only Unmapped Distribution"):
        transactions = [t for t in transactions if t.distribution_taction_id is None]
    if st.sidebar.checkbox("Only Unmapped Receipts"):
        transactions = [t for t in transactions if t.receipt_path is None]
    st.write(f"Filtered Transactions: {len(transactions)}")
    if len(transactions) > 0:
        current_transaction = transactions[st.number_input(
            "Current Index",
            min_value=0,
            step=1,
        )]
        st.write(current_transaction.model_dump())
        st.sidebar.markdown("Transaction Actions")
        database_transactions = list_to_df(DbHsaTransaction.load(db))
        if st.sidebar.checkbox("Assign Expense"):
            st.markdown("### Assign Expense")
            assign_expense(db, current_transaction, database_transactions)
        if st.sidebar.checkbox("Assign Distribution"):
            st.markdown("### Assign Distributions")
            assign_distribution(db, current_transaction, database_transactions)
        if st.sidebar.checkbox("Assign Receipt"):
            st.markdown("### Assign Receipt")
            assign_receipt(db, current_transaction)
    else:
        st.success("All transactions filtered!")

def assign_receipt(db: DbAccess, hsa_transaction: DbHsaTransaction):
    receipt_paths = {r.name: r for r in ReceiptPath.load(db)}
    selected_path = receipt_paths[st.selectbox(
        "Receipt Path", options=list(receipt_paths.keys())
    )]
    st.markdown(f"Selected path: `{selected_path.path}`")
    selected_filename = st.selectbox(
        "File to Assign", [f.name for f in list(selected_path.path.glob("*")) if f.is_file() and f.name[0] != "."]
    )
    total_path = selected_path.path / selected_filename
    st.markdown(f"Total path: {total_path}")
    if st.button("Assign Receipt Path"):
        st.success(f"Assigning `{total_path}` to ID: {hsa_transaction.id}")
        db.update_value(hsa_transaction, "receipt_path", total_path)

def assign_expense(db: DbAccess, hsa_transaction: DbHsaTransaction, database_transactions: pd.DataFrame):
    if hsa_transaction.expense_taction_id is not None:
        st.warning("HSA Transaction already has a expense assigned!")
    else:
        if st.checkbox("Manual Expense Assignment"):
            chosen_assignment = st.number_input(
                "Manual Transaction ID Assignment",
                min_value=0,
                step=1,
            )
            st.write(taction_table([Transaction.load_single(db, chosen_assignment)]))
        else:
            st.markdown("Matching Expenses")
            matching_transactions = taction_table(Transaction.load(db, amount=hsa_transaction.amount * NEGATIVE_ONE))
            matching_transactions["already_in_use"] = matching_transactions["id"].isin(database_transactions["expense_taction_id"])
            if st.checkbox("Filter Expenses Already In Use", value=True):
                matching_transactions = matching_transactions.loc[~matching_transactions["already_in_use"], :]
            st.write(matching_transactions)
            chosen_assignment = st.selectbox(
                "Transaction to Assign",
                options=list(matching_transactions["id"])
            )
        if st.button("Assign Expense"):
            st.success(f"Assigning Expense {chosen_assignment} to HSA transaction {hsa_transaction.id}")
            db.update_value(hsa_transaction, "expense_taction_id", chosen_assignment)
    
def assign_distribution(db: DbAccess, hsa_transaction: DbHsaTransaction, database_transactions: pd.DataFrame):
    if hsa_transaction.distribution_taction_id is not None:
        st.warning("HSA Transaction already has a distribution assigned!")
    else:
        st.markdown("Matching Distributions")
        matching_transactions = taction_table(Transaction.load(db, amount=hsa_transaction.amount))
        matching_transactions["already_in_use"] = matching_transactions["id"].isin(database_transactions["distribution_taction_id"])
        if st.checkbox("Filter Distributions Already In Use", value=True):
            matching_transactions = matching_transactions.loc[~matching_transactions["already_in_use"], :]
        st.write(matching_transactions)
        chosen_assignment = st.selectbox(
            "Transaction to Assign",
            options=list(matching_transactions["id"])
        )
        if st.button("Assign Distribution"):
            st.success(f"Assigning Distribution {chosen_assignment} to HSA transaction {hsa_transaction.id}")
            db.update_value(hsa_transaction, "distribution_taction_id", chosen_assignment)

def generate_unique_identifier(expense_data: pd.DataFrame) -> pd.Series:
    expense_data['id'] = expense_data['Expense Date'].astype(str) +\
                         expense_data['Expense'].str[0] +\
                         expense_data['Recipient/Patient'].str[0] +\
                         expense_data['Submitted Amount'].astype(str)
    if any(expense_data.duplicated()):
        st.markdown('Removing some duplicates...')
        duplicate_ids = set(expense_data.loc[expense_data.duplicated(), 'id'])
        new_lists = []
        for duplicate_id in duplicate_ids:
            duplicates = expense_data.loc[expense_data['id'] == duplicate_id, :].reset_index()
            duplicates['id'] = duplicates['id'] + duplicates.index.astype(str)
            new_lists.append(duplicates)
        new_lists.append(expense_data.loc[~expense_data['id'].isin(duplicate_ids), :])
        expense_data = pd.concat(new_lists)
    if any(expense_data.duplicated()):
        st.error("All rows not unique")
    expense_data = expense_data.rename(columns={"id": "unique_identifier"})
    return expense_data

