from pathlib import Path
from typing import ClassVar

from expense_tracker.common import DbItem, NamedItem

class ReceiptPath(DbItem, NamedItem):
    path: Path
    table_name: ClassVar[str] = "hsa_receipt_paths"