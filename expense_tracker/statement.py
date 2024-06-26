from typing import ClassVar, Optional

from expense_tracker.common import DbItem, AmountItem, DateItem, s_extend
from expense_tracker.account import Account
from expense_tracker.database import DbAccess, WhereDef
from expense_tracker.transaction import Transaction

class BaseStatement(AmountItem, DateItem, DbItem):
    statement_month: int
    statement_year: int
    description: str
    deferred: bool
    table_name: ClassVar[str] = "statement_transactions"

class DbStatement(BaseStatement):
    account_id: int
    taction_id: Optional[int] = None

    @property
    def base_fields(self) -> dict:
        return super().model_dump()
    
    def upgrade(self, account: Account, taction: Transaction):
        return Statement(
            **self.base_fields,
            account=account,
            taction=taction,
        )
    
    @classmethod
    def load(cls, db: DbAccess, unmapped_taction: bool = False, account_id: int = None, taction_id: int = None, where_list: list = None, **kwargs) -> list:
        if account_id is not None:
            where_list = s_extend(where_list, [WhereDef(field="account_id", value=account_id)])
        if unmapped_taction:
            where_list = s_extend(where_list, [WhereDef(field="taction_id", value="null", is_null=True)])
        if taction_id is not None:
            where_list = s_extend(where_list, [WhereDef(field="taction_id", value=taction_id)])
        return super().load(db, where_list=where_list, **kwargs)
    
    def unmap_taction(self, db: DbAccess):
        db.update_value(self, "taction_id", None)

class Statement(BaseStatement):
    account: Account
    taction: Optional[Transaction] = None

    @property
    def db_representation(self) -> DbStatement:
        DbStatement(
            **super().model_dump(),
            account_id=self.account.id,
            taction_id=self.taction.id,
        )