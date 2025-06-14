from enum import Enum
from typing import Optional, List
import yaml
from pydantic import BaseModel, Field


class ItemRelevanceDecision(BaseModel):
    """Decision on whether an item is relevant for the case."""

    is_relevant: bool = Field(description="Gibt an, ob der Prüfungspunkt relevant ist.")
    reason: str = Field("", description="Begründung für die Relevanzentscheidung.")


class BasePromptItem(BaseModel):
    id: Optional[str] = ""

    @classmethod
    def from_yaml(cls, path: str) -> "BasePromptItem":
        """Create an instance from a YAML dictionary."""
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return cls(**data)

    def to_yaml(self, path: str):
        """Save the instance as a YAML file."""
        with open(path, "w", encoding="utf-8") as f:
            yaml.dump(
                self.model_dump(), f, allow_unicode=True, default_flow_style=False
            )

    def task_as_prompt(self) -> List[dict]:
        raise NotImplementedError("Subclasses must implement this method.")

    def examples_as_prompt(self) -> List[dict]:
        raise NotImplementedError("Subclasses must implement this method.")


class SachverhaltItem(BasePromptItem):
    task: str
    example: Optional[str]

    def task_as_prompt(self) -> List[dict]:
        prompt = [{"role": "user", "content": f"{self.task}"}]
        return prompt

    def examples_as_prompt(self) -> List[dict]:
        return [{"role": "user", "content": self.example}]


# create enum with search types
class SearchType(Enum):
    """Enum for search types."""

    MOST_RECENT = "most_recent"
    SIMILAR_PARA = "similar_para"


class AbstrakteErwItem(BasePromptItem):
    task: str = ""
    examples: List[str] = []
    mandatory: bool = True
    requirement_for_analysis: Optional[str] = None
    search: Optional[SearchType] = None

    def task_as_prompt(self) -> List[dict]:
        prompt = [{"role": "user", "content": f"{self.task}"}]
        return prompt

    def examples_as_prompt(self) -> List[dict]:
        prompt = []
        for ex in self.examples:
            prompt.extend([{"role": "user", "content": ex}])
        return prompt

    def requirement_as_prompt(self) -> List[dict]:
        if self.requirement_for_analysis:
            return [{"role": "user", "content": f"{self.requirement_for_analysis}"}]
        return []


if __name__ == "__main__":

    # Load all YAML files from folder: "prompts/production/aerw/
    import os
    import glob
    from pathlib import Path

    folder_path = Path("../prompts/production/sach/")

    yaml_files = glob.glob(os.path.join(folder_path, "*.yaml"))
    # sort by numbering in filename
    yaml_files.sort(key=lambda x: int(Path(x).stem.split("_")[1]))

    for yaml_file in yaml_files:
        try:
            pp = SachverhaltItem.from_yaml(yaml_file)
        except Exception as e:
            print(f"Error loading {yaml_file}: {e}")
            continue
