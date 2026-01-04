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
    

"""Process columns."""

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
    print("Release date processed.")
    return df


def process_shading_units(df):
    """Converts shading units to integers."""
    col = 'shading_units'
    
    if col not in df.columns:
        return df

    def to_int(val):
        if pd.isna(val):
            return None
        try:
            # First convert to float to handle the ".0", then to int
            return int(float(val))
        except:
            return None

    df[col] = df[col].apply(to_int)
    df[col] = df[col].astype('Int64')
    print("Shading units converted.")
    return df



def process_clocks(df):
    """
    Cleans clock speeds and stops execution if an unexpected unit is found.
    Calculates max_clock_mhz from base and boost values.
    """
    clock_cols = ['base_clock', 'boost_clock']

    def validate_and_clean(val, col_name):
        # 1. Check for null or empty values (these are allowed)
        if pd.isna(val) or str(val).strip() == "":
            return None
        
        val_str = str(val).strip()
        
        # 2. Check if the value ends with ' MHz'
        if "MHz" in val_str:
            # Extract number and return as int
            return int(float(val_str.replace("MHz", "").strip()))
        else:
            # 3. If it's not null and not MHz, raise an error
            raise ValueError(
                f"\n[FATAL ERROR] Unexpected format in column '{col_name}': '{val_str}'\n"
                f"Cell value (raw): {val!r}\n"
                f"Cell value (stripped): '{val_str}'\n"
                f"Transformation stopped to prevent data corruption."
            )

    try:
        # Process each column with a custom check
        for col in clock_cols:
            if col in df.columns:
                # We use a lambda to pass the column name for better error reporting
                df[col] = df.apply(lambda row: validate_and_clean(row[col], col), axis=1)

        # Calculate max_clock_mhz
        df['max_clock_mhz'] = df[['base_clock', 'boost_clock']].max(axis=1)

        print("Clock speeds validated, cleaned and unified.")
        
    except ValueError as ve:
        print(ve)
        exit()
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        exit()
        
    return df

def process_memory_size(df):
    """Simplified memory conversion to KB."""
    col = 'mem_size'
    
    def convert(val):
        # Convert to string and upper case to handle all variants (gb, GB, Gb) (I hope there are no bits, just bytes)
        val = str(val).upper()
        
        try:
            #remove unit, convert to number and multiply
            if 'GB' in val:
                return int(float(val.replace('GB', '').strip()) * 1024 * 1024)
            
            if 'MB' in val:
                return int(float(val.replace('MB', '').strip()) * 1024)
            
            if 'KB' in val:
                return int(float(val.replace('KB', '').strip()))
                
        except:
            return None
        return None

    # Apply the logic and create the new column
    df['mem_size_kb'] = df[col].apply(convert)
    df['mem_size_kb'] = df['mem_size_kb'].astype('Int64')
    print("Memory size converted.")
    return df

def process_memory_bus(df):
    """Cleans memory bus width"""
    col = 'mem_bus'
    
    def convert_to_int(val):
        if pd.isna(val) or str(val).strip() == "":
            return None
        
        val_str = str(val).strip()
        
        # System Shared handling
        if val_str == "System Shared":
            return None
            
        # Strict check for 'bit'
        if "bit" in val_str:
            try:
                return int(val_str.replace("bit", "").strip())
            except:
                return None
        else:
            # Fatal error if unknown format found
            raise ValueError(f"[FATAL ERROR] Unexpected format in Memory Bus: '{val_str}'")

    try:
        df['mem_bus_bits'] = df[col].apply(convert_to_int)
        df['mem_bus_bits'] = df['mem_bus_bits'].astype('Int64')
        print("Memory bus width processed.")
    except ValueError as ve:
        print(ve)
        exit()
    return df

def process_bandwidth(df):
    """Creates a numeric bandwidth column and a boolean flag for system dependency."""
    
    col = 'bandwidth'
    
    def extract_info(val):
        if pd.isna(val) or str(val).strip() == "":
            return None, False
            
        v_str = str(val).strip()
        
        # 1. Handle System Dependent case
        if "System Dependent" in v_str or "System Shared" in v_str:
            return None, True
            
        # 2. Handle numeric cases with strict unit check
        try:
            mbs_value = None
            if "TB/s" in v_str:
                mbs_value = float(v_str.replace("TB/s", "").strip()) * 1024 * 1024
            elif "GB/s" in v_str:
                mbs_value = float(v_str.replace("GB/s", "").strip()) * 1024
            elif "MB/s" in v_str:
                mbs_value = float(v_str.replace("MB/s", "").strip())
            
            if mbs_value is not None:
                return mbs_value, False
        except Exception:
            pass

        # 3. Fail-fast if format is unknown
        raise ValueError(f"[FATAL ERROR] Unknown Bandwidth format: '{v_str}'")

    try:
        # We apply the function and split the result into two columns
        results = df[col].apply(extract_info)
        df['bandwidth_mbs'] = results.apply(lambda x: x[0])
        df['is_system_dependent'] = results.apply(lambda x: x[1])
        
        print("Memory Bandwidth processed (Numeric + Boolean flag).")
    except ValueError as ve:
        print(ve)
        exit()

    return df

def process_fp32(df):
    """Converts FP32 performance  GFLOPS (numeric)."""

    col = 'tflops_fp32'
    
    def convert_to_gflops(val):
        if pd.isna(val) or str(val).strip() == "":
            return None
            
        v_str = str(val).strip()
        
        try:
            if "TFLOPS" in v_str:
                return float(v_str.replace("TFLOPS", "").replace(",", "").strip()) * 1000
            if "GFLOPS" in v_str:
                return float(v_str.replace("GFLOPS", "").replace(",", "").strip())
        except Exception:
            pass

        raise ValueError(f"[FATAL ERROR] Unexpected FP32 format: '{v_str}'")

    try:
        df['fp32_gflops'] = df[col].apply(convert_to_gflops)
        print("Theoretical Performance (FP32) unified")
    except ValueError as ve:
        print(ve)
        exit()
        
    return df

def process_tdp(df):
    """Cleans TDP values. Converts Watts to numeric."""
    
    col = 'tdp'
    
    def clean_tdp(val):
        # Nulls or empty strings
        if pd.isna(val) or str(val).strip() == "":
            return None
        
        val_str = str(val).strip()
        
        # Unknowns
        if "unknown" in val_str:
            return None
            
        # Standard Watt values
        if "W" in val_str:
            try:
                return int(val_str.replace("W", "").strip())
            except Exception:
                pass
            
        raise ValueError(f"[FATAL ERROR] Unexpected format in TDP: '{val_str}'")

    try:
        df['tdp_watts'] = df[col].apply(clean_tdp)
        df['tdp_watts'] = df['tdp_watts'].astype('Int64')
        print("TDP values cleaned and converted to watts.")
    except ValueError as ve:
        print(ve)
        exit()
        
    return df

def process_price(df):
    """Cleans Launch Price, converts to integer."""
    col = 'launch_price'
    
    def clean_price(val):
        if pd.isna(val) or str(val).strip() == "":
            return None
        
        val_str = str(val).strip()
        
        # Strict check for USD
        if "USD" in val_str:
            try:
                # Remove 'USD', commas, and any leading '$' just in case
                clean_val = val_str.replace("USD", "").replace(",", "").replace("$", "").strip()
                return int(float(clean_val))
            except Exception:
                pass
        
        # Stop if format is unexpected
        raise ValueError(f"[FATAL ERROR] Unexpected format in Price: '{val_str}'")

    try:
        if col in df.columns:
            df[col] = df[col].apply(clean_price)
            df['launch_price'] = df['launch_price'].astype('Int64')
            print("Launch Price cleaned and converted to integer.")
    except ValueError as ve:
        print(ve)
        exit()
    
            
    return df

def handle_duplicates(df):
    # Search for duplicates based on all columns.

    # There were no duplicates in the original data,
    # The duplicates were created by removing columns.
    all_duplicates = df[df.duplicated(keep=False)]
    
    # Duplicate count
    duplicate_count = df.duplicated().sum()
    
    if duplicate_count > 0:
        print(f"--- duplicates found and removed: {duplicate_count} ---")
        # print(all_duplicates.sort_values(by='product_name'))
        
        df = df.drop_duplicates()
    else:
        print("--- no duplicates found ---\n")
    return df


def main():
    try:
        df = load_data()
        df = trim_dataset(df)

        if df is not None:

            """Process all columns."""
            df = rename_columns(df)
            # brand OK
            # product_name OK           
            df = process_dates(df)
            # gpu_name OK
            # gpu_codename OK
            df = process_shading_units(df)
            df = process_clocks(df)
            df = process_memory_size(df)
            # mem_type OK
            df = process_memory_bus(df)
            df = process_bandwidth(df)
            df = process_fp32(df)
            df = process_tdp(df)
            df = process_price(df)

            handle_duplicates(df)
            

            df.to_csv(OUTPUT_PATH, index=False)
            print(f"Saved to: {OUTPUT_PATH}")
            print(df.head(15))
            print("all done")
    except Exception as e:
        print(f"Chyba: {e}")



if __name__ == "__main__":
    main()
