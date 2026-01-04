import pandas as pd
from config import INPUT_PATH, OUTPUT_PATH, KEEP_COLUMNS


try:
    df = pd.read_csv(INPUT_PATH)
    print(df.head(5))

except FileNotFoundError:
    print(f"Error: file '{INPUT_PATH}' not found.")


def trim_dataset():
    try:
        print(f"Načítám: {INPUT_PATH}")
        df = pd.read_csv(INPUT_PATH)

        df_trimmed = df[KEEP_COLUMNS]
        df_trimmed.to_csv(OUTPUT_PATH, index=False)
        print("Dataset trimmed and saved.")

    except Exception as e:
        print(f"Nastala chyba: {e}")