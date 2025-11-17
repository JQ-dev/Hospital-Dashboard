"""
Explore worksheet database structure to find the right tables and columns
for calculating Medicare CCR and Bad Debt + Charity %
"""

import duckdb

WORKSHEET_DB_PATH = 'data/hospital_worksheets.duckdb'

print("=" * 80)
print("Exploring Worksheet Database Structure")
print("=" * 80)
print()

# Connect to worksheet database
con = duckdb.connect(WORKSHEET_DB_PATH, read_only=True)

# List all tables
tables = con.execute("SHOW TABLES").df()
print(f"Total tables: {len(tables)}")
print()
print("Available tables:")
for table in tables['name']:
    print(f"  - {table}")
print()

# For each table that might contain the data we need, show structure
target_tables = ['C000001', 'S100001', 'G200000', 'G300000']

for table_name in target_tables:
    if table_name in tables['name'].values:
        print("=" * 80)
        print(f"Table: {table_name}")
        print("=" * 80)

        # Show columns
        columns = con.execute(f"DESCRIBE {table_name}").df()
        print("Columns:")
        for _, col in columns.iterrows():
            print(f"  - {col['column_name']}: {col['column_type']}")
        print()

        # Show sample row
        sample = con.execute(f"SELECT * FROM {table_name} LIMIT 1").df()
        if not sample.empty:
            print("Sample row:")
            for col in sample.columns:
                print(f"  {col}: {sample[col].iloc[0]}")
        print()

        # Show row count
        count = con.execute(f"SELECT COUNT(*) as cnt FROM {table_name}").fetchone()[0]
        print(f"Total rows: {count:,}")
        print()

con.close()
