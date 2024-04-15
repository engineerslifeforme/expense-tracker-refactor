from typing import ClassVar

from expense_tracker.common import (
    DbItem, 
    NamedItem, 
    BalanceItem,
)
from expense_tracker.database import DbAccess

class Account(NamedItem, BalanceItem, DbItem):
    visibility: bool
    purpose: str
    table_name: ClassVar[str] = "account"
