import kagglehub
import pandas as pd
import os

def inspect_dataset(name):
    print(f"\n--- Downloading & Loading Dataset: {name} ---")
    try:
        path = kagglehub.dataset_download(name)
        print("Path to dataset files:", path)
        
        # find the first csv file
        csv_files = [f for f in os.listdir(path) if f.endswith('.csv')]
        if not csv_files:
            print("No CSV files found.")
            return

        for csv in csv_files:
            print(f"Reading {csv}...")
            df = pd.read_csv(os.path.join(path, csv))
            print("Columns:", list(df.columns))
            print("Total rows:", len(df))
            print(df.head(1).to_dict(orient="records"))
            break # Just do one
            
    except Exception as e:
        print(f"Error loading {name}: {e}")

if __name__ == "__main__":
    inspect_dataset("nudratabbas/healthcare-fraud-detection-dataset")
    inspect_dataset("mdmahfuzsumon/pharma-dataset-drug-classes-interactions-and-cli-pr")
    inspect_dataset("algozee/healthcare-disease-prediction-dataset")
