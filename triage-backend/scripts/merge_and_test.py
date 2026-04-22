import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel
import sys
import os

def main():
    base_model_name = "Qwen/Qwen2.5-0.5B-Instruct"
    adapter_dir = "/home/balaraj/META final/triage-backend/models/dpo_output_gpu/final"
    merged_dir = "/home/balaraj/META final/triage-backend/models/dpo_output_gpu/merged"

    print("=============================================")
    print("🧠 Triage DPO Final Model Tester")
    print("=============================================\n")

    print(f"1. Loading Base Model: {base_model_name}...")
    tokenizer = AutoTokenizer.from_pretrained(base_model_name)
    base_model = AutoModelForCausalLM.from_pretrained(
        base_model_name,
        torch_dtype=torch.float16,
        device_map="auto"
    )

    print(f"2. Loading your trained LoRA adapter from overnight...")
    model = PeftModel.from_pretrained(base_model, adapter_dir)

    print("3. Merging the adapter permanently with the base model (this takes a moment)...")
    # This physically injects your training into the base model parameters
    model = model.merge_and_unload()

    print("\nMerge complete! Creating final disk backup...")
    os.makedirs(merged_dir, exist_ok=True)
    model.save_pretrained(merged_dir)
    tokenizer.save_pretrained(merged_dir)
    print(f"Saved complete merged model to: {merged_dir}")

    print("\n✅ Successfully Loaded & Merged!")
    print("---------------------------------------------")
    print("You can now test the model. Try asking it clinical questions or giving it a hospital scenario.")
    print("Type 'exit' or 'quit' to stop.\n")

    while True:
        try:
            print("-" * 50)
            user_input = input("🗣️ You: ")
            if user_input.lower() in ['quit', 'exit']:
                break
                
            if not user_input.strip():
                continue

            # Format the conversation in the Qwen chat style with a strict system prompt
            messages = [
                {"role": "system", "content": "You are an expert clinical triage assistant. Only provide medical decisions based strictly on verified clinical pathways and the data provided. Do not hallucinate external policies or invent drug interactions."},
                {"role": "user", "content": user_input}
            ]
            
            text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
            inputs = tokenizer([text], return_tensors="pt").to(model.device)
            
            # Generate the response!
            outputs = model.generate(
                **inputs, 
                max_new_tokens=250, 
                temperature=0.2, # Very low temperature for strict medical adherence
                do_sample=True,
                pad_token_id=tokenizer.eos_token_id
            )
            
            response = tokenizer.decode(outputs[0][len(inputs.input_ids[0]):], skip_special_tokens=True)
            
            print(f"\n🩺 Triage AI: \n{response.strip()}\n")
            
        except KeyboardInterrupt:
            break

    print("\nExiting chat. To use this later without merging, just point systems to the 'merged' folder!")

if __name__ == "__main__":
    main()
