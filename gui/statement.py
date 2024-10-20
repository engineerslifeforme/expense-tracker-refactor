from decimal import Decimal
from datetime import date

import streamlit as st
import pandas as pd

from expense_tracker.database import DbAccess
from expense_tracker.statement import DbStatement
from expense_tracker.transaction import Transaction, DbTransaction
from expense_tracker.execute import execute_transaction
from expense_tracker.account import Account
from expense_tracker.common import ZERO

from helper_ui import (
    select_account, 
    amount_input, 
    taction_table,
    select_category,
    select_method,
)

FOURTEEN_DAYS = pd.Timedelta(days=14)

def statement_scanning(db: DbAccess):
    options = [
        "Upload",
        "Assignment",
        "Check",
        "Invalidate",
        "Search Statement Actions",
        "Unmap Transaction",
        "Search Transactions",
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
        check(db)
    elif mode == options[3]:
        invalidate(db)
    elif mode == options[4]:
        search(db)
    elif mode == options[5]:
        unmap_transaction(db)
    elif mode == options[6]:
        search_transactions(db)
    else:
        st.error(f"Unknown mode: {mode}")

def search_transactions(db: DbAccess):
    start = st.date_input("Start Date")
    end = st.date_input("End Date")
    account_id = None
    if st.checkbox("Filter Account"):
        account_id = select_account(db).id
    transactions = pd.DataFrame([t.model_dump() for t in DbTransaction.load(db, account_id=account_id, less_equal_date=end, greater_equal_date=start)])
    statements = pd.DataFrame([s.model_dump() for s in DbStatement.load(db, less_equal_date=end, greater_equal_date=start)])
    filtered = transactions.loc[~transactions["id"].isin(statements["taction_id"]), :]
    st.markdown(f"Transactions not mapped to statements: ({len(filtered)} of {len(transactions)})")
    st.write(filtered)
    
def unmap_transaction(db: DbAccess):
    statement_to_unmap = st.number_input(
        "Statement ID to unmap Transaction",
        min_value=0,
        step=1,
    )
    statement = DbStatement.load_single(db, statement_to_unmap)
    st.write(statement.model_dump())
    if st.button("Unmap Transaction"):
        statement.unmap_taction(db)
        st.success(f"Unmapped transaction from statement {statement.id}")

def check(db: DbAccess):
    statements = pd.DataFrame([s.model_dump() for s in DbStatement.load(db)])
    st.markdown("### No Duplicate Assignments")
    duplicated = statements["taction_id"].duplicated()
    
    if all(~duplicated):
        st.success("No duplicate mappings of statements to transactions")
    else:
        duplicate_mappings = statements[duplicated]["taction_id"]
        st.write(statements.loc[statements["taction_id"].isin(duplicate_mappings), :])
        st.error("Duplicate mappings of statements to transactions!")

    st.markdown("### No valid statements mapped to invalid transactions")
    transactions = pd.DataFrame([t.model_dump() for t in DbTransaction.load(db, valid=None)]).set_index("id")
    merged = statements.join(transactions, on="taction_id", rsuffix="_transaction")
    if all(merged["valid_transaction"]):
        st.success("All mapped transactions are valid")
    else:
        st.error("Not all mapped transactions are valid!")


def search(db: DbAccess):
    if st.checkbox("Filter by Account"):
        account_id = select_account(db).id
        statements = DbStatement.load(db, account_id=account_id)
    else:
        statements = DbStatement.load(db)
    statements = pd.DataFrame([s.model_dump() for s in statements])
    st.write(statements)

def invalidate(db: DbAccess):
    statement_to_invalidate = st.number_input(
        "Statement to Invalidate",
        min_value=0,
        step=1,
    )
    statement = DbStatement.load_single(db, statement_to_invalidate)
    st.write(statement.model_dump())
    if st.button("Invalidate"):
        st.success(f"Invalidating statement {statement.id}")
        statement.invalidate(db)

def assign(db: DbAccess):
    st.markdown("### Assign Statements to Transactions")
    account_id_filter = None
    if st.checkbox("Filter By Account"):
        account_id_filter = select_account(db, label_prefix="Filter").id
    all_statements = pd.DataFrame([i.model_dump() for i in DbStatement.load(db, account_id=account_id_filter)])
    unmapped = DbStatement.load(db, account_id=account_id_filter, unmapped_taction=True)
    st.markdown(f"{len(unmapped)} Unmapped statements")
    if st.button("Attempt Auto-Assign"):
        transactions = pd.DataFrame([i.model_dump() for i in DbTransaction.load(db)])
        for unmapped_item in unmapped:
            min_date = unmapped_item.date - FOURTEEN_DAYS
            max_date = unmapped_item.date + FOURTEEN_DAYS
            potential_matches = transactions.loc[
                (transactions["date"] > min_date) &
                (transactions["date"] < max_date) &
                (transactions["amount"] == unmapped_item.amount) &
                (transactions["account_id"] == unmapped_item.account_id) &
                (~transactions["id"].isin(all_statements["taction_id"].unique()))
            ]
            if len(potential_matches) == 1:
                assigning_taction = potential_matches["id"].values[0]
                st.success(f"Assigning statement {unmapped_item.id} to transaction {assigning_taction}")
                db.update_value(unmapped_item, "taction_id", assigning_taction)
        unmapped = DbStatement.load(db, account_id=account_id_filter, unmapped_taction=True)
    st.write(pd.DataFrame([i.model_dump() for i in unmapped]))
    quantity_to_show = st.number_input(
        "Quantity to View",
        value=20,
    )
    default_method = select_method(db)
    action_options = [
        "Nothing",
        "New",
        "Assign",
    ]
    new_actions = []
    assign_actions = []
    no_actions = []
    for i in range(min([quantity_to_show, len(unmapped)])):
        index = i + 1
        active = unmapped[i]
        st.markdown(f"**Unmapped #{index}**")
        left, middle, right = st.columns(3)
        category = select_category(
            db, 
            st_container=left,
            label_suffix=f"# {index}"
        )
        # date = right.date_input(
        #     f"Date #{index}",
        #     value=active.date,
        # )
        right.markdown(f"Date: {active.date}")
        # amount = amount_input(
        #     label_suffix=f"#{index}",
        #     allow_negative=True,
        #     default=active.amount,
        #     st_container=left,
        # )
        middle.markdown(f"Amount: ${active.amount}")
        description = st.text_input(
            f"Description #{index}",
            value=active.description,
        )
        matches = None
        action = st.radio(f"Action #{index}", options=action_options)
        try:        
            matches = taction_table(Transaction.load(db, amount=active.amount)).sort_values(by="date", ascending=False)
        except KeyError:
            pass
        
        if action == action_options[2]: # Assign
            if matches is None:
                st.error("No assignments available, defaulting to Nothing action")
            else:
                assign_taction_id = st.selectbox(
                    f"Transaction ID to Assign #{index}",
                    options=matches["id"]
                )
                assign_actions.append((active, assign_taction_id))
        elif action == action_options[1]:
            new_actions.append((
                active,
                category,
                active.date,
                active.account_id,
                active.amount,
                description,
            ))
        elif action == action_options[0]:
            no_actions.append(active.id)
        else:
            st.error(f"Unknown action selection: {action}")
        if matches is not None:
            st.write(matches)
        else:
            st.warning(f"No matches on ${active.amount}")
    if st.button("Execute Actions"):
        for no_action in no_actions:
            st.warning(f"No action for statement {no_action}")
        for new_action in new_actions:
            statement, category, date, account_id, amount, description = new_action
            taction, subs = execute_transaction(
                db,
                date,
                False, # transfer
                description,
                False, # receipt
                Account.load_single(db, active.account_id),
                default_method,
                [(amount, category)],
            )
            st.success(f"Created Transaction {taction.id} and Sub {subs[0].id} for statement {statement.id}")
            db.update_value(statement, "taction_id", taction.id)
        for statement, taction_id in assign_actions:
            db.update_value(statement, "taction_id", taction_id)
            st.success(f"Assigned statement {statement.id} to Transaction {taction_id}")

def find_possible_column(column_names: list, search_term: str) -> int:
    for index, name in enumerate(column_names):
        if search_term in name.lower():
            return index
    return 0

def upload(db: DbAccess):
    st.markdown("## Statement Scanning")
    uploaded_file = st.file_uploader("Choose a file")
    use_headers = "infer"
    today = date.today()
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
            value=today.month,
        )
        year = middle.number_input(
            "Statement Year",
            min_value=1950,
            step=1,
            max_value=2050,
            value=today.year,
        )
        account_id = select_account(db, st_container=right).id
        left, middle, right = st.columns(3)
        column_names = dataframe.columns
        date_column = left.selectbox(
            "Date Column",
            options=column_names,
            index=find_possible_column(column_names, "date"),
        )
        try:
            new_data["date"] = pd.to_datetime(dataframe[date_column]).dt.date
        except:
            middle.warning(f"Column `{date_column}` cannot be parsed as date")
        left, middle, right = st.columns(3)
        description_column = left.selectbox(
            "Description Column",
            options=column_names,
            index=find_possible_column(column_names, "description"),
        )
        new_data["description"] = dataframe[description_column]
        left, middle, right = st.columns(3)
        if left.checkbox("Split Credit/Debit"):
            credit_column = left.selectbox(
                "Credit Column",
                options=column_names,
                index=find_possible_column(column_names, "credit"),
            )
            dataframe[credit_column] = dataframe[credit_column].fillna("0.00")
            try:
                dataframe["credit"] = dataframe[credit_column].apply(Decimal)
            except:
                middle.warning(f"Column `{credit_column}` cannot be converted to decimal")
            debit_column = left.selectbox(
                "Debit Column",
                options=column_names,
                index=find_possible_column(column_names, "debit"),
            )
            dataframe[debit_column] = dataframe[debit_column].fillna("0.00")
            try:
                dataframe["debit"] = dataframe[debit_column].apply(Decimal) * Decimal("-1")
            except:
                middle.warning(f"Column `{debit_column}` cannot be converted to decimal")
            try:
                new_data["amount"] = dataframe["credit"] - dataframe["debit"]
            except:
                pass
        else:
            amount_column = left.selectbox(
                "Amount Column",
                options=column_names,
                index=find_possible_column(column_names, "amount"),
            )
            try:
                new_data["amount"] = dataframe[amount_column].apply(Decimal)
            except:
                middle.warning(f"Column `{amount_column}` cannot be converted to decimal")
        entries = len(new_data)
        negative_entries = len(new_data.loc[new_data["amount"] <ZERO, :])
        positive_entries = entries - negative_entries
        # Usually more debits than credits
        if st.checkbox("Flip Amount Sign", value=(positive_entries > negative_entries)):
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