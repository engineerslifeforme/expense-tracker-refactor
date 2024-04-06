from decimal import Decimal
from typing import ClassVar
from datetime import date

from expense_tracker.common import (
    DbItem,
    NamedItem,
    BalanceItem,
)
from expense_tracker.database import DbAccess
from expense_tracker.common import ZERO

class Budget(DbItem, NamedItem, BalanceItem):
    visibility: bool
    frequency: str # TODO Consider string enum
    increment: Decimal
    purpose: str
    table_name: ClassVar[str] = "budget"

    @property
    def monthly_increment_amount(self) -> Decimal:
        if self.frequency == "M":
            increment_add = self.increment
        elif self.frequency == "D":
            increment_add = self.increment * Decimal("365") / Decimal("12")
        elif self.frequency == "Y":
            increment_add = self.increment / Decimal("12")
        else:
            raise(ValueError(f"Budget {self.name} has unknown frequency: {self.frequency}"))
        return increment_add.quantize(ZERO)        
    
    def monthly_increment_balance(self, db: DbAccess, execution_date: date):
        self.add_to_balance(db, self.monthly_increment_amount)
        