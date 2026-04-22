"""Helpers for generating a Colab-friendly training notebook."""

from __future__ import annotations


def build_colab_cells(repo_url: str = "https://github.com/YOUR_TEAM/triage-backend") -> list[str]:
    """Return notebook cells for the demo-friendly Colab flow."""

    return [
        "!pip install fastapi pydantic sqlalchemy aiosqlite datasets trl peft accelerate pyyaml numpy",
        f"!git clone {repo_url}\nimport sys\nsys.path.insert(0, '/content/triage-backend')",
        "from triage.training.unsloth_trainer import setup_model\nmodel, tokenizer = setup_model('unsloth/gemma-3-4b-it-unsloth-bnb-4bit')",
        "from triage.training.trajectory_collector import TrajectoryCollector\ncollector = TrajectoryCollector(output_dir='/content/triage_data')",
        "from triage.training.preference_labeler import PreferenceLabeler\nlabeler = PreferenceLabeler()",
    ]
