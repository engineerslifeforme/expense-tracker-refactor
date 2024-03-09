from typing import ClassVar
from decimal import Decimal

from expense_tracker.common import DbItem, DateItem, AmountItem, s_extend
from expense_tracker.database import DbAccess, WhereDef
from expense_tracker.account import Account
from expense_tracker.method import Method

class BaseTrasaction(DbItem, AmountItem, DateItem):
    transfer: bool
    description: str
    receipt: bool
    not_real: bool
    table_name: ClassVar[str] = "taction"

class DbTransaction(BaseTrasaction):
    account_id: int
    method_id: int

    @property
    def base_fields(self) -> dict:
        return super().dict()
    
    def upgrade(self, account_map: dict, method_map: dict):
        return Transaction(
            **self.base_fields,
            account=account_map[self.account_id],
            method=method_map[self.method_id]
        )
    
    @classmethod
    def load(cls, db: DbAccess, amount: Decimal = None, where_list: list = None, **kwargs) -> list:
        if amount is not None:
            where_list = s_extend(where_list, [WhereDef(field="amount", value=amount)])        
        return super().load(db, where_list=where_list, **kwargs)

class Transaction(BaseTrasaction):
    account: Account
    method: Method

    @property
    def db_representation(self) -> DbTransaction:
        DbTransaction(
            **super().dict(),
            account_id=self.account.id,
            method_id=self.method.id,
        )

    @classmethod
    def load_single(cls, db: DbAccess, id: int) -> dict:
        account_map = {a.id: a for a in Account.load(db)}
        method_map = {m.id: m for m in Method.load(db)}
        return DbTransaction.load_single(db, id).upgrade(account_map, method_map)
    
    @classmethod
    def load(cls, db: DbAccess, **kwargs) -> list:
        account_map = {a.id: a for a in Account.load(db)}
        method_map = {m.id: m for m in Method.load(db)}
        return [t.upgrade(account_map, method_map) for t in DbTransaction.load(db, **kwargs)]




