from decimal import Decimal

import streamlit as st
import pandas as pd
import numpy as np

from expense_tracker.database import DbAccess
from expense_tracker.hsa_transactions import DbHsaTransaction, HsaTransaction
from expense_tracker.transaction import Transaction
from expense_tracker.sub import Sub, DbSub
from expense_tracker.receipt_paths import ReceiptPath
from expense_tracker.common import NEGATIVE_ONE
from helper_ui import (
    taction_table, 
    list_to_df,
    select_category,
    sub_table,
)

def delete_expense_assignment(*args):
    delete_assignment(*args, "Expense", "expense_taction_id")

def delete_distribution_assignment(*args):
    delete_assignment(*args, "Distribution", "distribution_taction_id")

def delete_receipt_assignment(*args):
    delete_assignment(*args, "Receipt", "receipt_path")

def delete_assignment(db: DbAccess, id_options: list, assignment_name: str, field_name: str):
    left, right = st.columns(2)
    selected_expense_to_delete = left.selectbox(
        f"HSA Transaction to Delete {assignment_name} Assignment",
        options=id_options
    )
    if st.checkbox(f"Show {assignment_name} Assignment Detaills"):
        transaction_to_edit = HsaTransaction.load_single(db, selected_expense_to_delete)
        st.write(transaction_to_edit.model_dump())
    if right.button(f"Delete {assignment_name} Assignment"):
        # Need to edit base item
        transaction_to_edit = DbHsaTransaction.load_single(db, selected_expense_to_delete)
        st.success(f"Delete {assignment_name} assignment from transaction ID: {selected_expense_to_delete}")
        db.update_value(transaction_to_edit, field_name, None)

def hsa_management(db: DbAccess):
    hsa_tasks = [
        "Assignment",
        "Upload Records",
        "Find Expenses to Claim",
        "Check Database",
        "Delete Assignments",
        "Search",
        "Invalidate Transaction",
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
    elif hsa_task == hsa_tasks[3]:
        check(db)
    elif hsa_task == hsa_tasks[4]:
        delete_assignments(db)
    elif hsa_task == hsa_tasks[5]:
        search(db)
    elif hsa_task == hsa_tasks[6]:
        invalidate(db)
    else:
        st.error(f"Unknown HSA task: {hsa_task}")

def invalidate(db: DbAccess):
    id_to_invalidate = st.number_input(
        "HSA Transaction ID to invalidate",
        min_value=0,
        step=1,
        value=1,
    )
    transaction_to_edit = HsaTransaction.load_single(db, id_to_invalidate)
    st.write(transaction_to_edit.model_dump())
    transaction_to_edit = DbHsaTransaction.load_single(db, id_to_invalidate)
    if st.button("Invalidate"):
        db.update_value(transaction_to_edit, "valid", False)

def search(db: DbAccess):
    st.write(pd.DataFrame([
        i.model_dump() for i in DbHsaTransaction.load(db)
    ]))

def delete_assignments(db: DbAccess):
    all_ids = [i.id for i in DbHsaTransaction.load(db)]
    delete_expense_assignment(
        db,
        all_ids,
    )
    delete_distribution_assignment(
        db,
        all_ids,
    )
    delete_receipt_assignment(
        db,
        all_ids,
    )

def check(db: DbAccess):
    st.markdown("### Checking Database Correctness")
    transactions = pd.DataFrame([t.model_dump() for t in DbHsaTransaction.load(db)])
    
    st.markdown("#### Duplicate Transaction to Expense Assignments?")
    expense_duplicates = transactions.loc[transactions["expense_taction_id"].duplicated(), "expense_taction_id"].unique()
    if len(expense_duplicates) < 1:
        st.success("All Expense Assignments unique!")
    else:
        st.error("Not all expense assignments unique!")
        nonunique = transactions.loc[transactions["expense_taction_id"].isin(list(expense_duplicates)), :]
        st.markdown(f"{len(nonunique)} Non-unique expense assignments:")
        st.write(nonunique)
        delete_expense_assignment(db, list(nonunique["id"]))
    
    st.markdown("#### Duplicate Transaction to Distribution Assignments?")
    distribution_duplicates = transactions.loc[transactions["distribution_taction_id"].duplicated(), "distribution_taction_id"].unique()
    if len(distribution_duplicates) < 1 or (len(distribution_duplicates) == 1 and np.isnan(distribution_duplicates[0])):
        st.success("All Distribution Assignments unique!")
    else:
        st.error("Not all Distribution assignments unique!")
        nonunique = transactions.loc[transactions["distribution_taction_id"].isin(list(distribution_duplicates)), :]
        st.markdown(f"{len(nonunique)} Non-unique distribution assignments:")
        st.write(nonunique)
        delete_distribution_assignment(db, list(nonunique["id"]))
    
    st.markdown("#### Duplicate Transaction to Receipt Assignments?")
    transactions_with_receipt = transactions.loc[~transactions["receipt_path"].isnull(), :]
    receipt_duplicates = transactions_with_receipt.loc[transactions_with_receipt["receipt_path"].duplicated(), "receipt_path"].unique()
    if len(receipt_duplicates) < 1:
        st.success("All Receipt Assignments unique!")
    else:
        st.error("Not all Receipt assignments unique!")
        nonunique = transactions.loc[transactions["receipt_path"].isin(list(receipt_duplicates)), :]
        st.markdown(f"{len(nonunique)} Non-unique receipt path assignments:")
        st.write(nonunique)
    st.markdown("#### Invalid Transaction with Mappings?")
    invalids = transactions.loc[~transactions["valid"], :]
    bad_mappings = []
    bad_mappings.extend(invalids.loc[~invalids["expense_taction_id"].isnull(), "id"])
    bad_mappings.extend(invalids.loc[~invalids["distribution_taction_id"].isnull(), "id"])
    bad_mappings.extend(invalids.loc[~invalids["receipt_path"].isnull(), "id"])
    bad_mappings = set(bad_mappings)
    if len(bad_mappings) < 1:
        st.success("No mappings on invalid transactions")
    else:
        st.error(f"Mappings existing on {len(bad_mappings)} invalid transactions!")
        st.write(transactions.loc[transactions["id"].isin(bad_mappings), :])
    # TODO: All assignments are to valid
    # TODO: Check expense, distribution amount match
    # TODO: Same dates with same amounts
    # TODO: All transactions mapped to distribution

def find_expenses(db: DbAccess):
    st.markdown("### Find Expenses to Claim")
    filter_category = select_category(db)
    if st.button("Show Expenses"):
        sub_df = pd.DataFrame([i.model_dump() for i in DbSub.load(db, category_id=filter_category.id)])
        st.markdown(f"Total Subs: {len(sub_df)}")
        existing_mappings = [i.expense_taction_id for i in DbHsaTransaction.load(db)]
        sub_df = sub_df.loc[~sub_df["taction_id"].isin(existing_mappings), :]
        st.markdown(f"{len(sub_df)} remaining after filtering already mapped")
        st.write(sub_table(Sub.upgrade_list(db, DbSub.df_to_list(sub_df))))


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
        db_records = list_to_df(DbHsaTransaction.load(db, valid=None))
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
            assign_receipt(db, current_transaction, database_transactions)
    else:
        st.success("All transactions filtered!")

def assign_receipt(db: DbAccess, hsa_transaction: DbHsaTransaction, database_transactions: pd.DataFrame):
    if hsa_transaction.receipt_path is not None:
        st.warning("HSA Transaction already has a receipt assigned!")
    else:
        receipt_paths = {r.name: r for r in ReceiptPath.load(db)}
        selected_path = receipt_paths[st.selectbox(
            "Receipt Path", options=list(receipt_paths.keys())
        )]
        st.markdown(f"Selected path: `{selected_path.path}`")
        def path_assignment(a, b):
            if a is None:
                return False
            else:
                return a.parent == b
        database_transactions["in_selected_dir"] = [path_assignment(i, selected_path) for i in database_transactions["receipt_path"].values]
        used_names = database_transactions.loc[database_transactions["in_selected_dir"], "receipt_path"]
        directory_filenames = [f.name for f in list(selected_path.path.glob("*")) if f.is_file() and f.name[0] != "." and f.name not in used_names]
        selected_filename = st.selectbox(
            "File to Assign", directory_filenames
        )
        if selected_filename is None:
            # Happens if it is not mounted on mac
            st.error(f"No files found in {selected_path.path}.  Is it available?")
        else:
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
            if chosen_assignment in database_transactions["expense_taction_id"].values:
                st.error(f"Expense ID {chosen_assignment} already assigned!")
            else:
                st.success(f"Expense ID {chosen_assignment} is not currently assigned to an HSA transaction")
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

