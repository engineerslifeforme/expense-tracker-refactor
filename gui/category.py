import streamlit as st

from expense_tracker.database import DbAccess
from expense_tracker.category import Category

def category(db: DbAccess):
    options = [
        "Data Check",
        "Invalidate",
    ]
    selected_mode = st.sidebar.radio(
        "Category Mode",
        options = options,
    )

    if selected_mode == options[0]:
        check(db)
    elif selected_mode == options[1]:
        invalidate(db)
    else:
        st.error(f"Unknown category mode: {selected_mode}")

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