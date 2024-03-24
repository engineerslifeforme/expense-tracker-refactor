import streamlit as st

from expense_tracker.database import DbAccess
from transaction_input import transaction_input
from hsa_management import hsa_management
from search import search
from category import category
from budget import budget

""" # Expense App """

db = DbAccess("example.db")

views = [
    "Transaction Input",
    "HSA Management",
    "Search",
    "Category",
    "Budget",
]

view = st.sidebar.radio(
    "Select View",
    options = views
)

if view == views[0]:
    transaction_input(db)
elif view == views[1]:
    hsa_management(db)
elif view == views[2]:
    search(db)
elif view == views[3]:
    category(db)
elif view == views[4]:
    budget(db)
else:
    st.error(f"Unknown view {view}")