from pathlib import Path
from decimal import Decimal
from typing import Union, Optional
from datetime import date

import sqlite3
import pandas as pd
from pydantic import BaseModel
import numpy as np

class WhereDef(BaseModel):
    field: str
    comparator: str = "="
    value: Union[Decimal, float, int, date, str]

    @property
    def sql(self) -> str:
        value = self.value
        if type(self.value) == str:
            value = "\"" + self.value + "\""
        return f"{self.field} {self.comparator} {value}"

class DbAccess(object):

    def __init__(self, path_to_database: Path):
        self.con = sqlite3.connect(path_to_database)
        self.cursor = self.con.cursor()
    
    def load_table(self, table_name: str, decimal_columns: list = None, date_columns: list = None, index: str = "id", where_list: list = None) -> pd.DataFrame:
        dtype = {}
        if decimal_columns is not None:
            dtype = {column: str for column in decimal_columns}
        sql = f"SELECT * FROM {table_name}"
        if where_list is not None:
            sql += f" WHERE {' AND '.join([w.sql for w in where_list])}"            
        print(f"Executing SQL: {sql}")
        data = pd.read_sql_query(
            sql,
            self.con,
            parse_dates=date_columns,
            dtype=dtype,
        )
        if decimal_columns is not None:
            for column in decimal_columns:
                data[column] = data[column].apply(Decimal)
        if index is not None:
            data = data.set_index(index)
        data = data.replace({np.nan: None})
        return data
    
    def get_next_id(self, cls) -> int:
        current_max = self.cursor.execute(f"SELECT MAX(id) FROM {cls.table_name}").fetchone()[0]
        # Returns None when table is empty
        if current_max is None:
            return 1
        else:
            return current_max + 1

    def insert(self, cls, names, values):
        names = ", ".join(names)
        compatible_values = []
        for value in values:
            if type(value) in [str, date, Optional[Path]]:
                compatible_values.append("\"" + str(value) + "\"")
            elif value is None:
                compatible_values.append("NULL")
            else:
                compatible_values.append(str(value))
        values = ", ".join(compatible_values)
        sql_statement = f"INSERT INTO {cls.table_name} ({names}) VALUES({values})"
        print(f"Attempting SQL:{sql_statement}")
        self.cursor.execute(sql_statement)
        self.con.commit()

    def update_value(self, object, field_name, new_value):
        value = new_value
        if object.model_fields[field_name].annotation in [str, Optional[Path]]:
            value = "\"" + str(value) + "\""
        if new_value is None:
            value = "null"
        sql = f"UPDATE {object.table_name} SET {field_name} = {value} WHERE id = {object.id}"
        print(f"Executing SQL: {sql}")
        self.con.execute(sql)
        self.con.commit()