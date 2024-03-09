from decimal import Decimal
from typing import ClassVar

from expense_tracker.common import (
    DbItem,
    NamedItem,
    BalanceItem,
)
from expense_tracker.database import DbAccess

class Budget(DbItem, NamedItem, BalanceItem):
    visibility: bool
    frequency: str # TODO Consider string enum
    increment: Decimal
    purpose: str
    table_name: ClassVar[str] = "budget"
        