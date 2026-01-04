import pandas as pd
import re
from config import INPUT_PATH, OUTPUT_PATH, KEEP_COLUMNS, RENAME_COLUMNS

def load_data():
    try:
        df = pd.read_csv(INPUT_PATH)
        print(f"Data loaded from: {INPUT_PATH}")
        return df

    except FileNotFoundError:
        print(f"Error: file '{INPUT_PATH}' not found.")
  

def trim_dataset(df):
    try:
        df_trimmed = df[KEEP_COLUMNS].copy()
        print("Dataset trimmed")
        return df_trimmed

    except Exception as e:
        print(f"Error: {e}")

def rename_columns(df):
    """Renames columns using the mapping from config.py."""
    try:
        df = df.rename(columns=RENAME_COLUMNS)
        print("Columns renamed")
        return df
    except Exception as e:
        print(f"Error during renaming: {e}")
        return df

def process_dates(df):
    """Year Month Day extraction from 'release_date' and delete original column."""
    date_col = 'release_date'
    
    # 1. Extraction of year number (4 digits starting with 19 or 20)
    df['Release_year'] = df[date_col].str.extract(r'((?:19|20)\d{2})')

    # 2. Extraction of month: We look for a word of at least 3 letters (Jan, Feb, October...)
    df['Release_month'] = df[date_col].str.extract(r'([a-zA-Z]{3,})')

    # 3. Extraction of day: We look for 1 to 2 digits followed by st, nd, rd, or th
    df['Release_day'] = df[date_col].str.extract(r'\b(\d{1,2})(?:st|nd|rd|th)\b')

    df = df.drop(columns=['release_date'])

    return df

def process_memory_size(df):
    """Simplified memory conversion to KB."""
    col = 'mem_size'
    
    def convert(val):
        # Convert to string and upper case to handle all variants (gb, GB, Gb)
        val = str(val).upper()
        
        try:
            if 'GB' in val:
                # Remove 'GB', convert to number and multiply
                return int(float(val.replace('GB', '').strip()) * 1024 * 1024)
            
            if 'MB' in val:
                # Remove 'MB', convert to number and multiply
                return int(float(val.replace('MB', '').strip()) * 1024)
            
            if 'KB' in val:
                # Just remove 'KB' and keep the number
                return int(float(val.replace('KB', '').strip()))
                
        except:
            # If there is "System Dependent" or empty value, return None
            return None
        return None

    # Apply the logic and create the new column
    df['mem_size_kb'] = df[col].apply(convert)
    return df


def main():
    try:
        df = load_data()
        df = trim_dataset(df)

        if df is not None:
            df = rename_columns(df)
            df = process_dates(df)
            df = process_memory_size(df)

            df.to_csv(OUTPUT_PATH, index=False)
            print(f"Saved to: {OUTPUT_PATH}")

            print(df.head(5))

            print('---')
            print(df[['product_name', 'base_clock', 'boost_clock']].iloc[1000:].head(10))

            print("all done")
    except Exception as e:
        print(f"Chyba: {e}")



if __name__ == "__main__":
    main()
