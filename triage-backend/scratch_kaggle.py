import kagglehub
import os

# Download latest version
path = kagglehub.dataset_download("prasad22/healthcare-dataset")

print("Path to dataset files:", path)
print("Files in dataset:")
for file in os.listdir(path):
    print("-", file)
    
    if file.endswith(".csv"):
        import pandas as pd
        df = pd.read_csv(os.path.join(path, file))
        print(f"\nFirst 5 records of {file}:")
        print(df.head())
        print(f"\nDataset Info for {file}:")
        print(df.info())

