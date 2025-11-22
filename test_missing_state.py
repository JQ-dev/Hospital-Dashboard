"""Check for missing state code providers"""
import duckdb

con = duckdb.connect('data/hospital_analytics.duckdb', read_only=True)

print('Sample provider numbers from state 1 in hospital_kpis:')
provs = con.execute("""
    SELECT DISTINCT Provider_Number
    FROM hospital_kpis
    WHERE Provider_Number >= 10000 AND Provider_Number < 20000
    ORDER BY Provider_Number
""").df()
print(provs)

print('\nCheck if these providers exist in balance_sheet:')
for p in provs['Provider_Number'].tolist():
    cnt = con.execute('SELECT COUNT(*) FROM balance_sheet WHERE Provider_Number = ?', [p]).fetchone()[0]
    print(f'  Provider {p}: {cnt} records in balance_sheet')

print('\nCheck revenue table:')
for p in provs['Provider_Number'].tolist()[:3]:
    cnt = con.execute('SELECT COUNT(*) FROM revenue WHERE Provider_Number = ?', [p]).fetchone()[0]
    print(f'  Provider {p}: {cnt} records in revenue')

con.close()
