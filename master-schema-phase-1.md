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

### Core Data Models
#### Master Schema Structure 

```python
class MasterSchema(BaseSchema):
    legal_type: str
    version: str
    created_date: datetime
    last_updated: datetime
    source_decisions: List[str]
    sections: List[MasterSection]
```

#### Master Section
```python
class MasterSection(BaseSchema):
    name: str  # "entscheid", "erwägungen", "sachverhalt"
    order: int
    paragraph_templates: List[ParagraphTemplate]
```

#### Paragraph Template (Core Data Model)
```python
class ParagraphTemplate(BaseSchema):
    number_pattern: str
    title_template: str  # Abstracted title for paragraph
    description_template: List[str]  # Abstracted descriptions for paragraph
    required: bool = True  # True if present in all decisions
    inclusion_criteria: List[str] = [] # Criteria for optional paragraphs, as true/false decision rules, empty list when required = True
    subparagraph_templates: List["ParagraphTemplate"] = []
    frequency: float = 1.0
    similar_paragraph_refs: List[(float, SourceParagraphRef)] = []  # References to source paragraphs for formulation lookup, float is similarity score
```

#### Source Paragraph Reference
```python
class SourceParagraphRef(BaseSchema):
    decision_id: str
    section: str
    paragraph_number: str
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
    - Group/cluster paragraphs that are semantically similar (based on title, description, text and hierarchical position)
    - For each group, propose an abstracted title and description for the master schema template
    - Indicate which source paragraphs belong to each group (for traceability)
  - Mark a paragraph as required if present in all input schemas, else optional (with inclusion_criteria = 'optional')
  - If non-mandatory paragraph, formulate inclusion criteria as true/false decision rules
  - Recursively process subparagraphs if present
- Assemble all paragraph templates into a `MasterSchema` object


### 3. Expected Output
- Print or serialize the resulting `MasterSchema` as yaml or JSON


## Implementation Checklist
- [ ] Define minimal Pydantic models
- [ ] Create 2-3 fake annotated input schemas (YAML files)
- [ ] Load fake schemas as Pydantic models
- [ ] Aggregate and cluster paragraphs using LLMs and logic (LangGraph/LangChain)
- [ ] Generate master schema templates from LLM output
- [ ] Demonstrate traceability of source paragraphs
- [ ] Print/serialize the master schema

## Time Management
- **Pydantic models & fake data**: 30 min
- **LLM-based aggregation & clustering**: 90 min
- **Testing, output, and documentation**: 30 min
- **Buffer**: 30 min
- **Total**: ≤ 4 hours

## Out of Scope
- Real data or draft generation
- Full LLM/agent pipeline or extensive prompt engineering
- Advanced validation, error handling

---
This plan ensures a minimal, focused, and risk-aware implementation for Phase 1, providing a solid foundation for later phases. 