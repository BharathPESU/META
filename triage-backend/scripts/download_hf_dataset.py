#!/usr/bin/env python3
import json
import random
from pathlib import Path
from datasets import load_dataset

ROOT = Path(__file__).resolve().parent.parent
OUTPUT_FILE = ROOT / "data" / "full_training" / "dpo_pairs.jsonl"

def download_and_append_dataset():
    print("Downloading advanced DPO dataset from HuggingFace (argilla/dpo-mix-7k)...")
    dataset = load_dataset("argilla/dpo-mix-7k", split="train")
    
    # Shuffle and pick a subset to keep training fast
    # We will pick 500 samples for this demonstration
    samples = list(dataset)
    random.seed(42)
    random.shuffle(samples)
    subset = samples[:500]
    
    print(f"Adding {len(subset)} new high-quality samples to our training split...")
    
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    added = 0
    with OUTPUT_FILE.open("a", encoding="utf-8") as f:
        for idx, row in enumerate(subset):
            # argilla/dpo-mix-7k contains 'chosen' and 'rejected'
            # each is a list of conversation turns. We'll format the prompt and responses.
            try:
                # The first item in chosen is usually user prompt
                prompt = row['chosen'][0]['content']
                chosen_response = row['chosen'][1]['content']
                rejected_response = row['rejected'][1]['content']
                
                pair = {
                    "prompt": prompt,
                    "chosen": chosen_response,
                    "rejected": rejected_response
                }
                f.write(json.dumps(pair) + "\n")
                added += 1
            except Exception as e:
                continue
                
    print(f"Successfully added {added} advanced samples to {OUTPUT_FILE}")

if __name__ == "__main__":
    download_and_append_dataset()
