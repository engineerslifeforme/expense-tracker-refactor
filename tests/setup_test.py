from decimal import Decimal
from pathlib import Path
from datetime import date
import sqlite3

from expense_tracker.database import DbAccess
from expense_tracker.account import Account
from expense_tracker.budget import Budget
from expense_tracker.category import Category
from expense_tracker.method import Method
from expense_tracker.common import ZERO
from expense_tracker.import_dates import ImportantDate

class DatabaseTest:

    def __init__(self):
        self.db_path = Path("test.db")
        self.con = setup_database(self.db_path)

    def clean(self):
        self.db_path.unlink()

def setup_database(db_path: Path):
    if db_path.exists():
        db_path.unlink()
    con = sqlite3.connect(db_path)
    con.execute("""CREATE TABLE `account` (
`id` int(11) NOT NULL DEFAULT '0',
`name` char(50) DEFAULT NULL,
`balance` decimal(10,2) DEFAULT NULL,
`valid` tinyint(1) DEFAULT NULL,
`visibility` tinyint(1) DEFAULT NULL,
`purpose` varchar(50) DEFAULT NULL,
PRIMARY KEY (`id`)
)""")
    con.execute("""CREATE TABLE `budget` (
`id` int(11) NOT NULL DEFAULT '0',
`name` char(50) DEFAULT NULL,
`visibility` tinyint(1) DEFAULT NULL,
`frequency` char(1) DEFAULT NULL,
`increment` decimal(10,2) DEFAULT NULL,
`balance` decimal(10,2) DEFAULT NULL,
`valid` tinyint(1) DEFAULT NULL,
`purpose` varchar(50) DEFAULT NULL,
PRIMARY KEY (`id`)
)""")
    con.execute("""CREATE TABLE `category` (
`id` int(11) NOT NULL DEFAULT '0',
`name` char(50) DEFAULT NULL,
`budget_id` int(11) DEFAULT NULL,
`valid` tinyint(1) DEFAULT NULL,
`no_kid_retire` decimal(3,2) DEFAULT NULL,
`kid_retire` decimal(3,2) DEFAULT NULL,
PRIMARY KEY (`id`)
)""")
    con.execute("""CREATE TABLE `sub` (
`id` int(11) NOT NULL DEFAULT '0',
`amount` decimal(10,2) DEFAULT NULL,
`category_id` int(11) DEFAULT NULL,
`taction_id` int(11) DEFAULT NULL,
`valid` tinyint(1) DEFAULT NULL,
`not_real` tinyint(1) DEFAULT NULL, date date,
PRIMARY KEY (`id`)
)""")
    con.execute("""CREATE TABLE `taction` (
`id` int(11) NOT NULL DEFAULT '0',
`date` date DEFAULT NULL,
`transfer` tinyint(1) DEFAULT NULL,
`account_id` int(11) DEFAULT NULL,
`method_id` int(11) DEFAULT NULL,
`description` text,
`receipt` tinyint(1) DEFAULT NULL,
`valid` tinyint(1) DEFAULT NULL,
`not_real` tinyint(1) DEFAULT NULL,
`amount` decimal(10,2) DEFAULT NULL,
PRIMARY KEY (`id`)
)""")
    con.execute("""CREATE TABLE `method` (
`id` int(11) NOT NULL DEFAULT '0',
`name` char(50) DEFAULT NULL,
`valid` tinyint(1) DEFAULT NULL,
PRIMARY KEY (`id`)
)""")
    con.execute("""CREATE TABLE `important_dates` (
`name` text NOT NULL,
`date` date NOT NULL, `valid` tinyint(1) DEFAULT NULL,
PRIMARY KEY (`name`)
)""")
    con.commit()
    db = DbAccess(db_path)
    important_date = ImportantDate(
        valid=True,
        name="test date",
        date=date(2024, 1, 1),
    )
    important_date.add_to_db(db)
    account = Account(
        balance=Decimal("100.00"),
        name="account",
        id = 1,
        valid = True,
        visibility= True,
        purpose="test",
    )
    account.add_to_db(db)
    budget = Budget(
        balance=Decimal("50.00"),
        name="budget",
        id=1,
        valid=True,
        visibility=True,
        frequency="M",
        increment=Decimal("10.00"),
        purpose="a test budget",
    )
    budget.add_to_db(db)
    category = Category(
        name="a category",
        id=1,
        valid=True,
        no_kid_retire=ZERO,
        kid_retire=ZERO,
        budget=budget,
    )
    category.add_to_db(db)
    method = Method(
        name="a method",
        id=1,
        valid=True,
    )
    method.add_to_db(db)
    return con
