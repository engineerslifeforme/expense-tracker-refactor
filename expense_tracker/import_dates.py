from typing import ClassVar
from datetime import date

from expense_tracker.common import (
    DbItem, 
    DateItem, 
    NamedItem,
    s_extend,
)
from expense_tracker.database import DbAccess, WhereDef

class ImportantDate(DateItem, NamedItem, DbItem):
    table_name: ClassVar[str] = "important_dates"
    
    @classmethod
    def load(cls, db: DbAccess, name: str = None, where_list: list = None, **kwargs) -> list:
        if name is not None:
            where_list = s_extend(where_list, [WhereDef(field="name", value=name, comparator="LIKE")])
        return super().load(db, where_list=where_list, **kwargs)
    
    def change_date(self, db: DbAccess, new_date: date):
        db.update_value(self, "date", new_date)