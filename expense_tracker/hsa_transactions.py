from pathlib import Path
from typing import ClassVar, Optional

from expense_tracker.common import DbItem, DateItem, AmountItem, s_extend
from expense_tracker.database import DbAccess, WhereDef

from expense_tracker.transaction import Transaction

class BaseHsaTransaction(DbItem, DateItem, AmountItem):
    unique_identifier: str
    receipt_path: Optional[Path] = None
    eob_path: Optional[Path] = None
    bill_path: Optional[Path] = None
    table_name: ClassVar[str] = "hsa_transactions"

class DbHsaTransaction(BaseHsaTransaction):
    expense_taction_id: Optional[int] = None
    distribution_taction_id: Optional[int] = None

    @property
    def base_fields(self) -> dict:
        return super().model_dump()
    
    def upgrade(self, expense: Transaction = None, distribution: Transaction = None):
        new = HsaTransaction(
            **self.base_fields,
        )
        if expense is not None:
            assert(expense.id == self.expense_taction_id)
            new.expense_taction = expense
        if distribution is not None:
            assert(distribution.id == self.distribution_taction_id)
            new.distribution_taction = distribution
        return new
    
    @classmethod
    def load(cls, db: DbAccess, expense_taction_id: int = None, distribution_taction_id: int = None, where_list: list = None, **kwargs) -> list:
        if expense_taction_id is not None:
            where_list = s_extend(where_list, [WhereDef(field="expense_taction_id", value=expense_taction_id)])
        if distribution_taction_id is not None:
            where_list = s_extend(where_list, [WhereDef(field="distribution_taction_id", value=distribution_taction_id)])
        return super().load(db, where_list=where_list, **kwargs)
    
    def unmap_expense_taction_id(self, db: DbAccess):
        db.update_value(self, "expense_taction_id", None)

    def unmap_distribution_taction_id(self, db: DbAccess):
        db.update_value(self, "distribution_taction_id", None)

class HsaTransaction(BaseHsaTransaction):
    expense_taction: Optional[Transaction] = None
    distribution_taction: Optional[Transaction] = None
    
    @classmethod
    def load(cls, db: DbAccess, **kwargs) -> list:
        return [
            h.upgrade(
                expense=Transaction.load_single(db, h.expense_taction_id),
                distribution=Transaction.load_single(db, h.distribution_taction_id),
            ) 
            for h in DbHsaTransaction.load(db, **kwargs)
        ]
    
    @classmethod
    def load_single(cls, db: DbAccess, id: int) -> dict:
        base = DbHsaTransaction.load_single(db, id)
        expense = None
        if base.expense_taction_id is not None:
            expense = Transaction.load_single(db, base.expense_taction_id)
        distribution = None
        if base.distribution_taction_id is not None:
            distribution = Transaction.load_single(db, base.distribution_taction_id)
        return base.upgrade(
            expense=expense,
            distribution=distribution,
        )