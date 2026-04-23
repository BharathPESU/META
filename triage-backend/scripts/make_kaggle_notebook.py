import json, re

with open("notebooks/kaggle_grpo_training.py", "r") as f:
    py_code = f.read()

# Split the code into cells based on the separator
separators = re.split(r'# ═══════════════════════════════════════════════════════════════════════════════\n# Cell \d+: .*?\n# ═══════════════════════════════════════════════════════════════════════════════\n', py_code)

cells = [
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "# 🏥 TRIAGE — GRPO Training on Kaggle\n",
    "Uses `transformers` + `trl` + `bitsandbytes` to fine-tune a 4B parameter model on Kaggle's T4/P100 GPUs."
   ]
  }
]

for part in separators:
    code = part.strip()
    if not code:
        continue
    
    # If there are pip commands, uncomment them
    lines = []
    for line in code.split("\n"):
        if line.startswith("# !pip"):
            lines.append(line[2:])
        else:
            lines.append(line)
    
    final_code = "\n".join(lines) + "\n"
    
    cells.append({
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [final_code]
    })

notebook = {
 "cells": cells,
 "metadata": {
  "accelerator": "GPU",
  "kernelspec": {
   "display_name": "Python 3",
   "name": "python3"
  },
  "language_info": {
   "name": "python"
  }
 },
 "nbformat": 4,
 "nbformat_minor": 0
}

with open("notebooks/triage_grpo_kaggle.ipynb", "w") as f:
    json.dump(notebook, f, indent=1)

print("Generated triage_grpo_kaggle.ipynb")
