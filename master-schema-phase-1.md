# Master Schema Phase 1: Minimal Prototype Plan

## Objective
Implement a minimal, single-file prototype that demonstrates the core logic of master schema generation from (fake) annotated input schemas. The implementation must be simple, focused, and address the most pressing risks, with a total effort not exceeding three hours.

## Core Technologies
- **Pydantic**: All data models must use Pydantic's `BaseModel` for type safety, validation, and serialization. This ensures compatibility with later phases and real data, and provides robust error checking even in the minimal prototype.
- **LangGraph / LangChain**: Any LLM/agent interaction must use LangGraph or LangChain. This provides a scalable, modular interface for LLM calls and ensures the prototype is future-proof for more complex agent workflows.
- **Python 3.11+**: The implementation will use modern Python features for clarity and maintainability.

**Rationale**: These technologies are chosen to ensure that even the minimal prototype is robust, extensible, and aligned with the project's long-term architecture. Pydantic models are easy to adapt and validate, and LangGraph/LangChain are the de facto standards for LLM orchestration in Python.

## Scope and Constraints
- **Only fake data** is used as input (no real court decisions).
- **Single file** implementation (in `experimental/master_schema_minimal.py`).
- **Bare minimum dataclasses** and logic to demonstrate the approach.
- **No draft generation** or downstream application—focus is on master schema creation only.
- **Minimal LLM/agent usage**: Minimal number of prompt/LLM calls to demonstrate feasibility.
- **Traceability**: Source paragraph references must be tracked, even in fake data.
- **Prompts**: Only the minimal prompt(s) needed for LLM/agent demonstration.

## Pressing Risks to Address
1. **Data/model mismatch**: Use flexible, minimal dataclasses; be ready to adapt.
2. **Annotation inconsistency**: Even in fake data, simulate minor inconsistencies to test LLM-based aggregation.
3. **Overfitting to fake data**: Make fake data realistic (simulate nested structure, optional/mandatory paragraphs, etc.).
4. **Prompt/LLM ambiguity**: Use a clear, simple prompt; document LLM output and limitations.
5. **Loss of source traceability**: Ensure every paragraph template in the master schema references its source(s).

## Minimal Data Model (Python Pydantic Pseudocode)
```python
from pydantic import BaseModel, Field
from typing import List, Optional

class SourceParagraphRef(BaseModel):
    decision_id: str
    section: str
    paragraph_number: str
    text: str

class ParagraphTemplate(BaseModel):
    number_pattern: str
    title_template: str
    description_template: List[str]
    required: bool = True
    inclusion_criteria: Optional[str] = None
    subparagraph_templates: List['ParagraphTemplate'] = Field(default_factory=list)
    source_paragraph_refs: List[SourceParagraphRef] = Field(default_factory=list)

class MasterSection(BaseModel):
    name: str
    order: int
    paragraph_templates: List[ParagraphTemplate]

class MasterSchema(BaseModel):
    legal_type: str
    version: str
    sections: List[MasterSection]
```

## Algorithmic Outline

### 1. Prepare Fake Annotated Input Schemas
- Create 2-3 fake input schemas (yaml files to load as Pydantic dataclasses) with:
  - Three sections: 'entscheid', 'erwägungen', 'sachverhalt'
  - Each section has a list of paragraphs (with numbers, text, and fake annotations: title, description)
  - Simulate both mandatory and optional paragraphs, and at least one nested (subparagraph) structure
  - Simulate minor inconsistencies (e.g., slightly different titles, numbering, or text) to test LLM-based aggregation

### 2. Aggregate and Cluster Paragraphs Using LLMs
- For each section across all input schemas:
  - Collect all paragraphs (with their numbers, text, titles, descriptions, and source references)
  - Use an LLM (via LangGraph/LangChain) to:
    - Group/cluster paragraphs that are semantically similar (based on title, description, and/or text)
    - For each group, propose a generic title and description for the master schema template
    - Indicate which source paragraphs belong to each group (for traceability)
  - Mark a paragraph as required if present in all input schemas, else optional (with inclusion_criteria = 'optional')
  - Recursively process subparagraphs if present
- Assemble all section templates into a `MasterSchema` object

### 3. (Optional) LLM/Agent Demonstration for Template Generation
- For one section or paragraph group, call an LLM/agent with a minimal prompt using LangGraph or LangChain:
  - Example prompt: "Given these paragraph texts and annotations, group similar paragraphs and suggest a generic title and description for each group as a master schema template."
  - Use the LLM output to define the `ParagraphTemplate` for each group
  - Document the prompt and output in the code

### 4. Output
- Print or serialize the resulting `MasterSchema` as yaml or JSON
- Print all source paragraph references for each template to demonstrate traceability

## Minimal Prompts (Example)
- "Given the following annotated paragraphs, group them by similarity and suggest a generic title and description for each group as a master schema template."
- Input: List of paragraph texts and their annotations
- Output: For each group: title, description, and list of source paragraph references

## Implementation Checklist
- [ ] Define minimal Pydantic models
- [ ] Create 2-3 fake annotated input schemas (YAML files)
- [ ] Load fake schemas as Pydantic models
- [ ] Aggregate and cluster paragraphs using LLMs (LangGraph/LangChain)
- [ ] Generate master schema templates from LLM output
- [ ] Demonstrate traceability of source paragraphs
- [ ] Print/serialize the master schema and traceability info

## Time Management
- **Pydantic models & fake data**: 30 min
- **LLM-based aggregation & clustering**: 60 min
- **[optional] LLM/agent integration & prompt**: 30 min
- **Testing, output, and documentation**: 30 min
- **Buffer**: 30 min
- **Total**: ≤ 3 hours

## Out of Scope
- Real data or draft generation
- Full LLM/agent pipeline or prompt engineering
- Advanced validation, error handling, or extensibility

---
This plan ensures a minimal, focused, and risk-aware implementation for Phase 1, providing a solid foundation for later phases. 