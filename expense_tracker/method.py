from typing import ClassVar

from expense_tracker.common import DbItem, NamedItem

class Method(NamedItem, DbItem):
    table_name: ClassVar[str] = "method"