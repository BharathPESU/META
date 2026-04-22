import os
import json
import random
import kagglehub
import pandas as pd

def convert_to_dpo():
    print("Downloading dataset...")
    path = kagglehub.dataset_download("prasad22/healthcare-dataset")
    csv_file = os.path.join(path, "healthcare_dataset.csv")
    
    df = pd.read_csv(csv_file)
    print(f"Loaded {len(df)} records. Converting to DPO format...")
    
    # We will sample 2000 records for speed, or we can do all 55k
    df = df.sample(n=min(len(df), 5000), random_state=42).reset_index(drop=True)
    
    dpo_pairs = []
    
    # Pre-fetch some random medications and results for 'rejected' samples
    meds = df['Medication'].unique().tolist()
    results = df['Test Results'].unique().tolist()
    
    for idx, row in df.iterrows():
        prompt = (f"Analyze Patient: {row['Age']} yo {row['Gender']}, Blood Type {row['Blood Type']}. "
                  f"Diagnosed with {row['Medical Condition']}. Adm: {row['Admission Type']}.\n"
                  f"Q: What medication should be prescribed and what are the expected test results?")
        
        chosen = f"Recommended Medication: {row['Medication']}.\nExpected Test Results: {row['Test Results']}."
        
        # Create a harder rejected response!
        # The model distinguishes them too easily. Let's make it look plausible.
        wrong_med = row['Medication']
        wrong_res = "Inconclusive" if row['Test Results'] == "Normal" else "Normal"
        
        # Inject subtle incorrect clinical phrasing
        rejected = f"Recommended Medication: {wrong_med}. However, the patient does not need strict observation.\nExpected Test Results: {wrong_res}."
        
        dpo_pairs.append({
            "prompt": prompt,
            "chosen": chosen,
            "rejected": rejected
        })
    
    out_dir = "/home/balaraj/META final/triage-backend/data/full_training"
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "healthcare_dpo.jsonl")
    
    with open(out_path, "w") as f:
        for pair in dpo_pairs:
            f.write(json.dumps(pair) + "\n")
            
    print(f"Successfully saved {len(dpo_pairs)} DPO training pairs to {out_path}")

if __name__ == "__main__":
    convert_to_dpo()
