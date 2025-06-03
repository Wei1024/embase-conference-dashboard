import pandas as pd
import openpyxl

# Load the Excel file
excel_file = 'conference_list.xlsx'

# Get all sheet names
wb = openpyxl.load_workbook(excel_file, read_only=True)
sheet_names = wb.sheetnames
print(f"Sheet names: {sheet_names}")
wb.close()

# Analyze each sheet
for sheet_name in sheet_names:
    print(f"\n{'='*60}")
    print(f"Sheet: {sheet_name}")
    print('='*60)
    
    # Read the sheet
    df = pd.read_excel(excel_file, sheet_name=sheet_name)
    
    print(f"Shape: {df.shape}")
    print(f"\nColumns: {list(df.columns)}")
    print(f"\nFirst 5 rows:")
    print(df.head())
    
    # Check for null values
    print(f"\nNull values per column:")
    print(df.isnull().sum())
    
    # Data types
    print(f"\nData types:")
    print(df.dtypes)