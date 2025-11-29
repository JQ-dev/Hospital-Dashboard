import pandas as pd
import os

# List of years
years = range(2020, 2025)

# List to hold dataframes
dfs = []

for year in years:
    file_path = f'data/source_data/HOSP10FY{year}/HOSP10_{year}_rpt.csv'
    if os.path.exists(file_path):
        df = pd.read_csv(file_path, header=None)
        # Extract columns 0, 2 (col2, col3) and 6 (col7)
        df_extracted = df[[0, 2, 6]].copy()
        df_extracted.columns = ['col1', 'col2', 'date']
        # Set multiindex
        df_extracted = df_extracted.set_index(['col1', 'col2'])
        # Extract year from date
        df_extracted['year'] = pd.to_datetime(df_extracted['date'], errors='coerce').dt.year
        dfs.append(df_extracted)

# Concatenate all
all_df = pd.concat(dfs)

# Drop rows where year is NaN
all_df = all_df.dropna(subset=['year'])

# Get unique index tuples and years
unique_values = all_df.index.unique()
unique_years = sorted(all_df['year'].unique())

# Create the table
table = pd.DataFrame(0, index=unique_values, columns=unique_years)

# Fill the table
for idx in unique_values:
    for yr in unique_years:
        mask = (all_df.index.get_level_values('col1') == idx[0]) & \
               (all_df.index.get_level_values('col2') == idx[1]) & \
               (all_df['year'] == yr)
        if mask.any():
            table.loc[idx, yr] = 1

# Save to CSV
table.to_csv('extracted_table.csv')

print("Table created and saved to extracted_table.csv")
print(table.head())