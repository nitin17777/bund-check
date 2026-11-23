import sys
sys.path.insert(0, r'D:\bund-check\backend')
from sqlalchemy import create_engine, inspect

engine = create_engine('sqlite:///./test.db')
inspector = inspect(engine)
tables = inspector.get_table_names()
print('Tables:', tables)
for table in tables:
    columns = inspector.get_columns(table)
    print(f'Table: {table}')
    for c in columns:
        print(f'  {c["name"]}: {c["type"]}')