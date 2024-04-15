from datetime import date
from decimal import Decimal
from pathlib import Path

from pydantic import BaseModel
from typing import ClassVar, Optional, Union

from expense_tracker.database import DbAccess, WhereDef

ONE = Decimal("1.00")
NEGATIVE_ONE = Decimal("-1")
ZERO = Decimal("0.00")

def s_extend(current_list: list, new_list: list) -> list:
    try:
        current_list.extend(new_list)
        return current_list
    # current_list is None
    except AttributeError:
        return new_list

class BaseDbItem(BaseModel):
    valid: bool
    table_name: ClassVar[str] = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        assert(self.table_name is not None)

    @classmethod
    def decimal_columns(cls) -> list:
        return [n for n, f in cls.model_fields.items() if f.annotation == Decimal]
    
    @classmethod
    def date_columns(cls) -> list:
        return [n for n, f in cls.model_fields.items() if f.annotation == date]
    
    @classmethod
    def load(cls, db: DbAccess, valid:bool = True, where_list: list = None, **kwargs) -> list:
        if valid is not None:
            where_list = s_extend(where_list, [WhereDef(field="valid", value=valid)])
        return [
            cls(**info) for info in 
            db.load_table(
                cls.table_name, 
                decimal_columns=cls.decimal_columns(),
                date_columns=cls.date_columns(),
                index=None,
                where_list=where_list,
                **kwargs)
            .to_dict(orient="records")
        ]
    
    def add_to_db(self, db: DbAccess):
        names = []
        values = []
        for name, field in self.model_fields.items():
            if field.annotation in [Decimal, float, str, date, int, Optional[Path], Optional[int]]:
                names.append(name)
                values.append(getattr(self, name))
            elif field.annotation == Union:
                import pdb;pdb.set_trace()
            elif field.annotation == bool:
                names.append(name)
                raw_value = getattr(self, name)
                if raw_value:
                    values.append(1)
                else:
                    values.append(0)
            else:
                names.append(f"{name}_id")
                try:
                    values.append(getattr(self, name).id)
                except AttributeError:
                    import pdb;pdb.set_trace()
        db.insert(self, names, values)

    def invalidate(self, db: DbAccess):
        db.update_value(self, "valid", False)

class DbItem(BaseDbItem):
    id: int    
    
    @classmethod
    def load_single(cls, db: DbAccess, id: int) -> dict:
        id_where = WhereDef(
            field="id",
            comparator="=",
            value=id,
        )
        return cls(**db.load_table(
            cls.table_name, 
            decimal_columns=cls.decimal_columns(),
            date_columns=cls.date_columns(),
            index=None,
            where_list=[id_where]) \
        .to_dict(orient="records")[0])      


class DateItem(BaseModel):
    date: date

    @classmethod
    def load(cls, *args, less_than_date: date = None, less_equal_date: date = None, greater_than_date: date = None, greater_equal_date: date = None, where_list: list = None, **kwargs):
        if less_than_date is not None:
            where_list = s_extend(where_list, [WhereDef(field="date", value=less_than_date, comparator="<")])
        if less_equal_date is not None:
            where_list = s_extend(where_list, [WhereDef(field="date", value=less_equal_date, comparator="<=")])
        if greater_than_date is not None:
            where_list = s_extend(where_list, [WhereDef(field="date", value=greater_than_date, comparator=">")])
        if greater_equal_date is not None:
            where_list = s_extend(where_list, [WhereDef(field="date", value=greater_equal_date, comparator=">=")])
        return super().load(*args, where_list=where_list, **kwargs)

class NamedItem(BaseModel):
    name: str

    def change_name(self, db: DbAccess, new_name: str):
        db.update_value(self, "name", new_name)

class BalanceItem(BaseModel):
    balance: Decimal

    def modify_balance(self, db: DbAccess, amount: Decimal) -> Decimal:
        # TODO: deprecate this in favor of add_to_balance
        new_balance = self.balance + amount
        db.update_value(self, "balance", new_balance)
        self.balance = new_balance
        return new_balance
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Without this pydantic reads .00 out of the database
        # and truncates, so 100.00 shows up as 100
        self.balance = self.balance.quantize(ZERO)

    def add_to_balance(self, db:DbAccess, change: Decimal) -> Decimal:
        self.balance += change
        db.update_value(self, "balance", self.balance)
        return self.balance

class AmountItem(BaseModel):
    amount: Decimal

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Without this pydantic reads .00 out of the database
        # and truncates, so 100.00 shows up as 100
        self.amount = self.amount.quantize(ZERO)