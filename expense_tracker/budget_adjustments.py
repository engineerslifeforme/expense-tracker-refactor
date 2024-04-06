from typing import ClassVar

from expense_tracker.common import DbItem, DateItem, AmountItem
from expense_tracker.budget import Budget
from expense_tracker.database import DbAccess

class BaseBudgetAdjustment(DbItem, DateItem, AmountItem):
    transfer: bool
    periodic_update: bool
    table_name: ClassVar[str] = "budget_adjustments"

class DbBudgetAdjustment(BaseBudgetAdjustment):
    budget_id: int

    @property
    def base_fields(self) -> dict:
        return super().dict()

    def upgrade(self, budget_map: dict):
        return BudgetAdjustment(
            **self.base_fields,
            budget=budget_map[self.budget_id],
        )

class BudgetAdjustment(BaseBudgetAdjustment):
    budget: Budget

    @classmethod
    def load_single(cls, db: DbAccess, id: int) -> dict:
        budget_map = {b.id: b for b in Budget.load(db, valid=None)}
        return DbBudgetAdjustment.load_single(db, id).upgrade(budget_map)
    
    @classmethod
    def load(cls, db: DbAccess, **kwargs) -> list:
        budget_map = {b.id: b for b in Budget.load(db, valid=None)}
        return [c.upgrade(budget_map) for c in DbBudgetAdjustment.load(db, **kwargs)]
    