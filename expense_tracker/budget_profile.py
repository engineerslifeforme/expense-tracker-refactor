from typing import ClassVar
from decimal import Decimal
from pathlib import Path

from expense_tracker.common import BaseDbItem
from expense_tracker.budget import Budget
from expense_tracker.database import DbAccess

class BaseBudgetProfile(BaseDbItem):
    month_1: Decimal
    month_2: Decimal
    month_3: Decimal
    month_4: Decimal
    month_5: Decimal
    month_6: Decimal
    month_7: Decimal
    month_8: Decimal
    month_9: Decimal
    month_10: Decimal
    month_11: Decimal
    month_12: Decimal
    table_name: ClassVar[str] = "budget_profile"

    @property
    def month_values(self) -> list:
        field_data = self.model_dump()
        return_list = list()
        for index in range(1,13):
            return_list.append(field_data[f"month_{index}"])
        return return_list
    
    @property
    def month_labels(self) -> list:
        return [
            "Jan",
            "Feb",
            "Mar",
            "Apr",
            "May",
            "Jun",
            "Jul",
            "Aug",
            "Sep",
            "Oct",
            "Nov",
            "Dec",
        ]

class DbBudgetProfile(BaseBudgetProfile):
    budget_id: int

    @property
    def base_fields(self) -> dict:
        return super().dict()

    def upgrade(self, budget_map: dict):
        return BudgetProfile(
            **self.base_fields,
            budget=budget_map[self.budget_id],
        )

class BudgetProfile(BaseBudgetProfile):
    budget: Budget

    @classmethod
    def load_single(cls, db: DbAccess, id: int) -> dict:
        budget_map = {b.id: b for b in Budget.load(db, valid=None)}
        return DbBudgetProfile.load_single(db, id).upgrade(budget_map)
    
    @classmethod
    def load(cls, db: DbAccess, **kwargs) -> list:
        budget_map = {b.id: b for b in Budget.load(db, valid=None)}
        return [c.upgrade(budget_map) for c in DbBudgetProfile.load(db, **kwargs)]

if __name__ == "__main__":
    db = DbAccess(Path("gui/example.db"))
    DbBudgetProfile.load(db)