from typing import ClassVar
from decimal import Decimal

from expense_tracker.common import DbItem, s_extend, AmountItem
from expense_tracker.category import Category
from expense_tracker.transaction import Transaction
from expense_tracker.database import DbAccess, WhereDef

class BaseSub(DbItem, AmountItem):
    not_real: bool
    table_name: ClassVar[str] = "sub"

class DbSub(BaseSub):
    category_id: int
    taction_id: int

    @property
    def base_fields(self) -> dict:
        return super().model_dump()

    def upgrade(self, category: Category, transaction: Transaction):
        assert(category.id == self.category_id)
        assert(transaction.id == self.taction_id)
        return Sub(
            **self.base_fields,
            category=category,
            taction=transaction,
        )
    
    @classmethod
    def load(cls, db: DbAccess, amount: Decimal = None, category_id: int = None, taction_id: int = None, where_list: list = None, **kwargs) -> list:
        if taction_id is not None:
            where_list = s_extend(where_list, [WhereDef(field="taction_id", value=taction_id)])
        if category_id is not None:
            where_list = s_extend(where_list, [WhereDef(field="category_id", value=category_id)])
        if amount is not None:
            where_list = s_extend(where_list, [WhereDef(field="amount", value=amount)])        
        return super().load(db, where_list=where_list, **kwargs)

class Sub(BaseSub):
    category: Category
    taction: Transaction

    @classmethod
    def load(cls, db: DbAccess, taction_id: int = None, where_list: list = None, **kwargs) -> list:
        if taction_id is not None:
            where_list = s_extend(where_list, [WhereDef(field="taction_id", value=taction_id)])
        return [
            s.upgrade(
                Category.load_single(db, s.category_id),
                Transaction.load_single(db, s.taction_id)
            )
            for s in DbSub.load(db, where_list=where_list, **kwargs)
        ]