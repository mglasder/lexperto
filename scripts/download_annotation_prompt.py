#!/usr/bin/env python3
"""
Download annotation prompt from LangSmith and save it locally for offline use.
"""

import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from dotenv import load_dotenv
from langsmith import Client

load_dotenv()

def download_annotation_prompt():
    """Download the annotation prompt from LangSmith and save it locally."""
    langsmith_client = Client()
    
    annotation_dir = Path("prompts/annotation")
    annotation_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        prompt = langsmith_client.pull_prompt("annotate_paragraphs", include_model=False)
        
        # Create filename with metadata
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        metadata = prompt.metadata
        filename = (
            f"{timestamp}_annotate_paragraphs_{metadata['lc_hub_commit_hash']}.txt"
        )
        
        prompt_file = annotation_dir / filename
        with open(prompt_file, "w", encoding="utf-8") as f:
            f.write(prompt.template)
        
        print(f"Prompt saved to: {prompt_file}")
        return prompt_file
        
    except Exception as e:
        print(f"Error downloading prompt: {e}")
        return None

if __name__ == "__main__":
    result = download_annotation_prompt()
 