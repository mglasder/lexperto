from typing import Optional, List
import yaml
from pydantic import BaseModel

class PruefungspunktAbstrErw(BaseModel):
    task: str = ""
    examples: List[str] = []
    mandatory: bool = True
    requirement_for_analysis: Optional[str] = None

    def task_as_prompt(self) -> List[dict]:
        prompt = [{"role": "user",
                   "content": f"{self.task}"}]
        return prompt

    def examples_as_prompt(self) -> List[dict]:
        prompt = []
        for example in self.examples:
            prompt.extend({"role": "user",
                           "content": example})
        return prompt

    @classmethod
    def from_yaml(cls, path: str) -> "PruefungspunktAbstrErw":
        """Create an instance from a YAML dictionary."""
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return cls(**data)

    def to_yaml(self, path: str):
        """Save the instance as a YAML file."""
        with open(path, "w", encoding="utf-8") as f:
            yaml.dump(self.model_dump(), f, allow_unicode=True, default_flow_style=False)

if __name__ == "__main__":

    # Load all YAML files from folder: "prompts/aerw/
    import os
    import glob
    from pathlib import Path
    folder_path = Path("prompts/aerw/")
    yaml_files = glob.glob(os.path.join(folder_path, "*.yaml"))
    for yaml_file in yaml_files:
        try:
            pp = PruefungspunktAbstrErw.from_yaml(yaml_file)
            print(f"Loaded: {yaml_file} with task: {pp.task}")
        except Exception as e:
            print(f"Error loading {yaml_file}: {e}")