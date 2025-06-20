import yaml
from datetime import datetime
from typing import List, Tuple
from pydantic import Field
import sys
import os

# Add the project root to the Python path to allow imports from `src`
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


# Correctly import BaseSchema from the project's models
from src.models.extraction import BaseSchema


# --- Core Data Models from master-schema-phase-1.md ---

class SourceParagraphRef(BaseSchema):
    """Reference to a source paragraph in an original decision."""
    decision_id: str
    section: str
    paragraph_number: str


class ParagraphTemplate(BaseSchema):
    """Template for a paragraph in the master schema."""
    number_pattern: str
    title_template: str = Field(description="Abstracted title for the paragraph.")
    description_template: List[str] = Field(description="Abstracted descriptions for the paragraph.")
    required: bool = Field(default=True, description="True if present in all decisions.")
    inclusion_criteria: List[str] = Field(default_factory=list, description="Criteria for optional paragraphs, as true/false decision rules.")
    subparagraph_templates: List["ParagraphTemplate"] = Field(default_factory=list)
    frequency: float = Field(default=1.0, description="How often this paragraph appears across decisions.")
    similar_paragraph_refs: List[Tuple[float, SourceParagraphRef]] = Field(default_factory=list, description="References to source paragraphs for formulation lookup, with similarity score.")


class MasterSection(BaseSchema):
    """A section in the master schema, like 'sachverhalt' or 'erwägungen'."""
    name: str  # "entscheid", "erwägungen", "sachverhalt"
    order: int
    paragraph_templates: List[ParagraphTemplate]


class MasterSchema(BaseSchema):
    """The master schema for a legal document type."""
    legal_type: str
    version: str
    created_date: datetime
    last_updated: datetime
    source_decisions: List[str]
    sections: List[MasterSection]


# --- Fake Data Loading and Preparation ---

# The plan specifies using `CourtDecisionStructured` and `ParagraphStructAnnotated`
# from the existing codebase to model the input schemas. We need to import them.
from src.models.extraction import CourtDecision, ParagraphStructAnnotated, Section, MetaData
from src.structuring import CourtDecisionStructured, SectionStructured


def load_annotated_decisions(directory: str) -> List[CourtDecisionStructured]:
    """Loads all annotated decision YAML files from a directory."""
    decisions = []
    for filename in os.listdir(directory):
        if filename.endswith(".yaml"):
            path = os.path.join(directory, filename)
            # We use CourtDecisionStructured because our fake data mimics
            # the structure of already annotated and structured decisions.
            decision = CourtDecisionStructured.from_yaml_file(path)
            decisions.append(decision)
    return decisions


if __name__ == "__main__":
    # Define the directory containing the fake annotated schemas
    fake_data_dir = "data/schemas/fake_annotated"

    # Load the fake decisions
    annotated_decisions = load_annotated_decisions(fake_data_dir)

    print(f"Successfully loaded {len(annotated_decisions)} fake annotated decisions.")
    for decision in annotated_decisions:
        print(f"  - {decision.meta.aktenzeichen}") 