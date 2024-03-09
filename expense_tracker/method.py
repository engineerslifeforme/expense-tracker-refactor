from typing import ClassVar

from expense_tracker.common import DbItem, NamedItem

class Method(DbItem, NamedItem):
    table_name: ClassVar[str] = "method"