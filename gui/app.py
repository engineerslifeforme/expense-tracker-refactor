import streamlit as st

from expense_tracker.database import DbAccess
from gui.transaction import transaction
from hsa_management import hsa_management
from search import search
from category import category
from budget import budget
from account import account
from statement import statement_scanning

st.set_page_config(layout="wide")

""" # Expense App """

db = DbAccess("example.db")

views = [
    "Transaction",
    "HSA Management",
    "Search",
    "Category",
    "Budget",
    "Account",
    "Statement Scanning",
]

view = st.sidebar.radio(
    "Select View",
    options = views
)

if view == views[0]:
    transaction(db)
elif view == views[1]:
    hsa_management(db)
elif view == views[2]:
    search(db)
elif view == views[3]:
    category(db)
elif view == views[4]:
    budget(db)
elif view == views[5]:
    account(db)
elif view == views[6]:
    statement_scanning(db)
else:
    st.error(f"Unknown view {view}")