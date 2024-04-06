from decimal import Decimal

import streamlit as st
import pandas as pd

from expense_tracker.database import DbAccess
from expense_tracker.account import Account
from expense_tracker.method import Method
from expense_tracker.category import Category
from expense_tracker.budget import Budget

def select_account(db: DbAccess, **kwargs) -> Account:
    return _select(db, Account, "Account", **kwargs)

def select_method(db: DbAccess, **kwargs) -> Method:
    return _select(db, Method, "Method", **kwargs)

def select_category(db: DbAccess, **kwargs) -> Category:
    return _select(db, Category, "Category", **kwargs)

def select_budget(db: DbAccess, **kwargs) -> Budget:
    return _select(db, Budget, "Budget", **kwargs)

def _select(db: DbAccess, DataType, label: str, label_suffix: str = None, label_prefix: str = None, st_container = None):
    if st_container is None:
        st_container = st
    if label_prefix is not None:
        label = " ".join([label_prefix, label])
    if label_suffix is not None:
        label = " ".join([label, label_suffix])
    items = DataType.load(db)
    name_map = {a.name: a for a in items}
    return name_map[st_container.selectbox(
        label,
        options = list(name_map.keys()),
    )]

def amount_input(label_suffix = None, st_container = None, allow_negative: bool = False, balance: bool = False, default: Decimal = None) -> Decimal:
    if st_container is None:
        st_container = st
    if balance:
        label = "Balance"
    else:
        label = "Amount"
    if label_suffix is not None:
        label = " ".join([label, label_suffix])
    min_value = 0.00
    if allow_negative:
        min_value = None
    if default is not None:
        default = float(default)
    else:
        default = 0.0
    return Decimal(st_container.number_input(
        label,
        min_value=min_value,
        step=0.01,
        value=default,
    ))

def list_to_df(pydantic_list: list) -> pd.DataFrame:
    return pd.DataFrame([m.dict() for m in pydantic_list])

def taction_table(taction_list: list) -> pd.DataFrame:
    dict_list = []
    for taction in taction_list:
        dict_data = taction.dict()
        dict_data["account"] = taction.account.name
        dict_data["method"] = taction.method.name
        dict_list.append(dict_data)
    df = pd.DataFrame(dict_list)
    try:
        df = df.sort_values(by=["date"], ascending=False)
    except KeyError:
        pass
    df["amount"] = df["amount"].astype(float)
    return df

def sub_table(sub_list: list) -> pd.DataFrame:
    dict_list = []
    for sub in sub_list:
        dict_data = sub.model_dump()
        dict_data["category"] = sub.category.name
        dict_data["description"] = sub.taction.description
        dict_data["date"] = sub.taction.date
        dict_data["transaction_id"] = sub.taction.id
        dict_data["receipt_present"] = sub.taction.receipt
        dict_data["account"] = sub.taction.account.name
        del(dict_data["taction"])
        dict_list.append(dict_data)
    return pd.DataFrame(dict_list)