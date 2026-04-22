"""
Colab DPO Dataset Builder
--------------------------
Copy and paste this exact script into a Google Colab code block! 
It will automatically download all 3 Kaggle datasets, combine them, 
and output a massive `large_triage_dpo.jsonl` file ready for high-end Colab training!

Prerequisites in Colab cell 1:
!pip install -q kagglehub pandas
"""

import kagglehub
import pandas as pd
import json
import random
import os

def load_first_csv(base_path):
    csvs = [f for f in os.listdir(base_path) if f.endswith('.csv')]
    if not csvs: return None
    return pd.read_csv(os.path.join(base_path, csvs[0]))

def main():
    print("⬇️ Downloading Kaggle Datasets into Colab...")
    
    # 1. Disease Dataset
    p1 = kagglehub.dataset_download("algozee/healthcare-disease-prediction-dataset")
    df_disease = load_first_csv(p1)
    
    # 2. Pharma Dataset
    p2 = kagglehub.dataset_download("mdmahfuzsumon/pharma-dataset-drug-classes-interactions-and-cli-pr")
    df_pharma = load_first_csv(p2)
    
    # 3. Fraud Dataset
    p3 = kagglehub.dataset_download("nudratabbas/healthcare-fraud-detection-dataset")
    df_fraud = load_first_csv(p3)

    print(f"✅ Loaded: {len(df_disease)} Diseases, {len(df_pharma)} Drugs, {len(df_fraud)} Fraud Records.")
    print("🧬 Synthesizing Large DPO Dataset...")

    dpo_records = []
    
    # We will generate thousands of high-quality training pairs
    system_prompt = "You are an expert clinical triage assistant. Only provide medical decisions based strictly on verified clinical pathways."

    # Mix 1: Patient Disease vs Safe Drug
    # We teach the model to safely recommend workups instead of blindly prescribing
    for i in range(len(df_disease)):
        patient = df_disease.iloc[i]
        
        # Pick 3 random drugs
        random_drugs = df_pharma.sample(3)
        drug_name = random_drugs.iloc[0]['brand_name']
        side_effect = random_drugs.iloc[0]['side_effects']
        
        prompt = f"A {patient['Age']} year-old {patient['Gender']} presents with BMI {patient['BMI']:.1f}, Blood Pressure: {patient['Blood Pressure']}, and Cholesterol: {patient['Cholesterol']}. The patient requests a prescription for {drug_name}."
        
        # Chosen: cautious, test-first behavior
        chosen = f"Clinical assessment: Patient has risk factors including {patient['Blood Pressure']} Blood Pressure. Directly prescribing {drug_name} without an attending physician is strictly prohibited. Given the risks (e.g. {side_effect}), the patient must undergo a comprehensive metabolic panel and physical examination first. Priority queue: Moderate."
        
        # Rejected: Hallucinated/unsafe behavior
        rejected = f"Based on the symptoms, giving {drug_name} is perfectly safe. Let me write that prescription right now to save time. Do not worry about their blood pressure."
        
        dpo_records.append({
            "system": system_prompt,
            "prompt": prompt,
            "chosen": [{"role": "assistant", "content": chosen}],
            "rejected": [{"role": "assistant", "content": rejected}]
        })

    # Mix 2: Fraud Detection & Diagnostics (From the Fraud Dataset)
    # We teach the model to identify suspicious claim geometries mathematically
    for i in range(len(df_fraud)):
        if i >= 5000: break # Grab 5000 records
        claim = df_fraud.iloc[i]
        
        prompt = f"Review ER Claim {claim['Claim_ID']}: Patient age {claim['Patient_Age']} ({claim['Patient_Gender']}). Diagnosis Code: {claim['Diagnosis_Code']}. Claim Amount: ${claim['Claim_Amount']}. Days between service and claim: {claim['Days_Between_Service_and_Claim']}. Specialty: {claim['Provider_Specialty']}."
        
        if claim['Is_Fraud'] == 1:
            chosen = f"Claim flagged for secondary review. The metrics provided (Age {claim['Patient_Age']}, Amount ${claim['Claim_Amount']}) require manual underwriting verification for Fraud Risk."
            rejected = f"This looks normal! Go ahead and approve the claim for ${claim['Claim_Amount']}."
        else:
            chosen = f"Claim passed preliminary automated checks. The delta of {claim['Days_Between_Service_and_Claim']} days is acceptable. Proceed with standard processing for {claim['Provider_Specialty']}."
            rejected = f"Fraud! Reject this completely due to the patient's age!"
            
        dpo_records.append({
            "system": system_prompt,
            "prompt": prompt,
            "chosen": [{"role": "assistant", "content": chosen}],
            "rejected": [{"role": "assistant", "content": rejected}]
        })

    # Output to disk
    output_path = "large_triage_dpo.jsonl"
    with open(output_path, "w") as f:
        for record in dpo_records:
            f.write(json.dumps(record) + "\n")

    print(f"\n🎉 SUCCESS! Generated {len(dpo_records)} massive DPO training pairs!")
    print(f"File saved to: {output_path}")

if __name__ == "__main__":
    main()
