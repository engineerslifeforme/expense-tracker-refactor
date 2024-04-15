from decimal import Decimal
from typing import ClassVar

from expense_tracker.common import (
    DbItem,
    NamedItem,
)
from expense_tracker.budget import Budget
from expense_tracker.database import DbAccess

class BaseCategory(NamedItem, DbItem):
    table_name: ClassVar[str] = "category"

class DbCategory(BaseCategory):
    budget_id: int

    @property
    def base_fields(self) -> dict:
        return super().dict()

    def upgrade(self, budget_map: dict):
        return Category(
            **self.base_fields,
            budget=budget_map[self.budget_id],
        )

class Category(BaseCategory):
    budget: Budget

    @property
    def db_representation(self) -> DbCategory:
        DbCategory(
            **super().dict(),
            budget_id=self.budget.id,
        )

    @classmethod
    def load_single(cls, db: DbAccess, id: int) -> dict:
        budget_map = {b.id: b for b in Budget.load(db, valid=None)}
        return DbCategory.load_single(db, id).upgrade(budget_map)
    
    @classmethod
    def load(cls, db: DbAccess, **kwargs) -> list:
        budget_map = {b.id: b for b in Budget.load(db, valid=None)}
        return [c.upgrade(budget_map) for c in DbCategory.load(db, **kwargs)]