# Master Schema Implementation Plan

## Overview

This document outlines the implementation plan for creating a master schema system that aggregates and standardizes individual court decision schemas of the same legal type. The ultimate goal is to enable the (semi-)automatic generation of high-quality first drafts of court decisions, reusing as much as possible the formalized language and structure from past decisions. The latter (second sentence) is out of scope for this part of the project.

## Key Principles and Updates

- **Core Goal**: Generate a master schema from the individual annotated input schema.

- **Formulation Reuse**: For many paragraphs, the language is highly formalized and should be reused verbatim or with minimal changes. Each paragraph template in the master schema must reference its source paragraphs, so that the exact formulations can be looked up and reused in draft generation.
- **Title/Description Abstraction**: The master schema's `title` and `description` fields are generic and abstract, but if paragraphs are nearly identical across decisions, these fields can be reused as-is. Otherwise, they should be abstracted to capture the general legal function of the paragraph.
- **Section/Paragraph Assumptions**: All three sections (`entscheid`, `erwägungen`, `sachverhalt`) are always present. Only paragraphs are distinguished as mandatory (present in all decisions) or optional (with criteria for inclusion).

## Out of scope

- **Court Decision Draft Generation**: Although the final goal is to generate a court decision draft given the master schema and other information input sources, this is out of scope for this part of the project.

## Master Schema Design

### Core Data Models (preliminary)

#### Master Schema Structure 
```python
class MasterSchema(BaseSchema):
    legal_type: str
    version: str
    created_date: datetime
    last_updated: datetime
    source_decisions: List[str]
    sections: List[MasterSection]
    metadata_template: MetaDataTemplate
```

#### Master Section
```python
class MasterSection(BaseSchema):
    name: str  # "entscheid", "erwägungen", "sachverhalt"
    order: int
    paragraph_templates: List[ParagraphTemplate]
```

#### Paragraph Template (Updated)
```python
class ParagraphTemplate(BaseSchema):
    number_pattern: str
    title_template: str  # Abstract/generic, but reused if identical
    description_template: List[str]  # Abstract/generic, but reused if identical
    required: bool = True  # True if present in all decisions
    inclusion_criteria: Optional[str] = None  # Criteria for optional paragraphs
    subparagraph_templates: List["ParagraphTemplate"] = []
    legal_concepts: List[str] = []
    frequency: float = 1.0
    source_paragraph_refs: List[SourceParagraphRef] = []  # References to source paragraphs for formulation lookup
```

#### Source Paragraph Reference
```python
class SourceParagraphRef(BaseSchema):
    decision_id: str
    section: str
    paragraph_number: str
    text: str  # The actual formulation to be reused
```

#### Meta Data Template
```python
class MetaDataTemplate(BaseSchema):
    required_fields: List[str] = []
    optional_fields: List[str] = []
    field_patterns: Dict[str, str] = {}
```

## Implementation Phases (Minimal, Iterative Approach)

### Phase 1: Minimal Prototype (Fake Data, Single File)
- **Goal**: Establish a running system with the real data types and absolutely minimal functionality for master schema generation and application (draft generation), using only fake data.
- **File Structure**: Single file (e.g., `src/master_schema_minimal.py`).
- **Functionality**:
  - Define all core data models (MasterSchema, MasterSection, ParagraphTemplate, SourceParagraphRef, etc.) in the minimal necessary degree of detail
  - Create a fake input schema with anotations with a few sections and paragraph templates, each referencing fake source paragraphs.
  - Implement a minimal master schema generation algorithm using the minimum number of llms/ agents for that
  - Draft minimal prompts needed for these llms/ agents

### Phase 2: MVP with Real Annotated Decisions (Single File)
- **Goal**: Extend Phase 1 to use real annotated court decisions as input, producing a master schema from real data. Core functionality should not be extended. The main difference to Phase 1 is the use of real data to generate a real master schema.
- **File Structure**: Still a single file (e.g., `src/master_schema_mvp.py`).
- **Functionality**:
  - Parse a small set of real annotated decisions.
  - Extract section and paragraph patterns, including references to real source paragraphs.
  - Generate a master schema from real data.
  - Improve prompts

### **The following phases are preliminary and subject to revision after the implementation of the first two phase**

### Phase 3: Schema Analysis and Pattern Extraction (Extend MVP)
- **Goal**: Extend the MVP to analyze all available annotated schemas, extract patterns, and compute frequency and similarity statistics.
- **Functionality**:
  - Analyze all annotated schemas in the dataset.
  - Identify mandatory vs. optional paragraphs (based on frequency across cases).
  - Cluster similar paragraphs and abstract titles/descriptions as needed.
  - Update the master schema with extracted patterns and source references.

### Phase 4: Master Schema Generation (Extend MVP)
- **Goal**: Extend the MVP to generate a more complete master schema from the extracted patterns.
- **Functionality**:
  - Generate paragraph templates with frequency thresholds.
  - Abstract or reuse titles/descriptions as appropriate.
  - Include source references for all templates.
  - Output the master schema as a YAML or JSON file.

### Phase 5: Master Schema Validation (New Functionality)
- **Goal**: Add validation functionality to check compliance of individual schemas with the master schema.
- **Functionality**:
  - Validate that all mandatory paragraphs are present in a given decision.
  - Check for correct use of formulations (reuse of source text where required).
  - Report deviations and suggest corrections.

### Phase 6: Master Schema Iterative Update (New Functionality)
- **Goal**: Enable iterative updates to the master schema as new decisions are added or patterns change.
- **Functionality**:
  - Update frequency statistics and paragraph templates as new data arrives.
  - Add new source references and adjust inclusion criteria as needed.
  - Support versioning and change tracking for the master schema.

## Minimal File Structure (Phases 1-2)
```
src/
  master_schema_minimal.py  # Phase 1
  master_schema_mvp.py      # Phase 2 (can replace minimal.py)
```

## Reasoning for Updates

- **Source Paragraph References**: Added to ParagraphTemplate to enable direct lookup and reuse of formalized language, supporting the goal of high-quality draft generation.
- **Title/Description Abstraction**: Clarified that these are generic in the master schema, but can be reused verbatim if paragraphs are nearly identical; otherwise, they should be abstracted.
- **Section/Paragraph Assumptions**: Simplified to always include all three sections, with only paragraphs being mandatory/optional, reflecting the observed data and simplifying schema logic.
- **Minimal, Iterative Phases**: Redefined phases to start with a minimal, fake-data prototype in a single file, then extend to MVP with real data, and only then add more advanced analysis, generation, validation, and update features. This ensures rapid prototyping and early feedback, while keeping the codebase minimal and focused.
- **Minimal File Structure**: Emphasized a single-file approach for early phases to reduce complexity and speed up iteration.

This plan ensures that the master schema system is built incrementally, with a strong focus on formulation reuse and practical draft generation, while keeping the implementation as simple as possible in the early stages.

## Core Risks to Address in Phases 1 and 2

The following risks must be carefully considered and mitigated during the first two phases to ensure the master schema approach is valid, robust, and extensible:

### 1. Data/Model Mismatch
- **Risk**: The data models (MasterSchema, ParagraphTemplate, etc.) may not accurately reflect the structure or variability of the real annotated input schemas.
- **Mitigation**: Design models to be flexible and extensible; validate against a variety of real annotated schemas early; iterate on the data model as soon as mismatches are detected.

### 2. Annotation Inconsistency
- **Risk**: The input annotated schemas may have inconsistencies in section/paragraph naming, numbering, or annotation style, making automated extraction and aggregation error-prone.
- **Mitigation**: Implement normalization and validation routines for input schemas; document and handle edge cases; flag and review inconsistencies manually in the MVP phase.

### 3. Overfitting to Small/Fake Data
- **Risk**: The minimal prototype (Phase 1) may lead to design choices that do not generalize to real data, especially if fake data is too simplistic or not representative.
- **Mitigation**: Use fake data that mimics real-world complexity as much as possible; move to real data (Phase 2) as early as feasible; be prepared to refactor based on real-world findings.

### 4. Prompt/LLM Ambiguity and Drift
- **Risk**: Prompts for LLMs/agents may be ambiguous, leading to inconsistent or low-quality master schema generation; LLM outputs may drift or be non-deterministic.
- **Mitigation**: Draft and iteratively refine prompts; test with multiple LLM runs; document prompt versions and results; consider adding minimal post-processing/validation of LLM output.

### 5. Loss of Source Traceability
- **Risk**: If source paragraph references are not tracked or are lost during aggregation, the master schema will not support formulation reuse or traceability, undermining a core goal.
- **Mitigation**: Make source reference tracking a non-negotiable requirement in all aggregation logic; test traceability in both fake and real data scenarios.

### 6. Extensibility for Later Phases
- **Risk**: Early design decisions (e.g., hardcoding, lack of modularity) may make it difficult to extend the system for analysis, validation, or iterative update in later phases.
- **Mitigation**: Keep code modular and well-documented; avoid premature optimization but design with extensibility in mind; review and refactor after Phase 2 as needed.

### 7. Minimal Viable Prompts and LLM Usage
- **Risk**: Using too few or overly simplistic prompts/LLMs in Phase 1 may not surface real-world challenges in LLM-based schema generation.
- **Mitigation**: Even in the minimal prototype, experiment with at least one realistic prompt/LLM interaction; document limitations and lessons learned for Phase 2.

By proactively addressing these risks, the project will be better positioned to deliver a robust and extensible master schema system, and to avoid costly rework in later phases. 