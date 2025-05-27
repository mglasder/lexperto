from typing import Optional
from pydantic import BaseModel, Field
from enum import Enum
from pathlib import Path
import yaml

class Role(str, Enum):
    USER = "user"
    SYSTEM = "system"

class BasePrompt(BaseModel):
    role: Role = Field(..., description="The role of the message sender (user, system)")
    content: str = Field(..., description="The content of the message")

class UserPrompt(BasePrompt):
    role: Role = Role.USER

class SystemPrompt(BasePrompt):
    role: Role = Role.SYSTEM

class ParagraphPrompt(BaseModel):
    id: str = Field(..., description="Unique identifier for the prompt (e.g., 'prompt_1')")
    description: str = Field(..., description="Description of what the prompt is used for")
    instruction: UserPrompt = Field(..., description="Instruction for the prompt")
    example: Optional[UserPrompt] = Field(None, description="Example of expected output or usage")

    @classmethod
    def from_yaml(cls, yaml_path: Path) -> 'ParagraphPrompt':
        """Create a ParagraphPrompt instance from a YAML file."""

        with open(yaml_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        return cls(**data)


if __name__ == "__main__":
    p = ParagraphPrompt.from_yaml(Path("prompts/para_1_prompt.yaml"))
    print(p)
    