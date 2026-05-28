# Architecture Overview

This document provides a high-level map of the Lexperto processing flow and how prompts and tests relate to pipeline stages.

```mermaid
flowchart LR
    A[Input Documents] --> B[Extraction]
    B --> C[Structuring]
    C --> D[Annotation]
    D --> E[Outputs]

    P[Prompts] -. guide behavior .-> B
    P -. guide behavior .-> C
    P -. guide behavior .-> D

    T[Tests] -. validate outputs .-> B
    T -. validate outputs .-> C
    T -. validate outputs .-> D
    T -. validate artifacts .-> E
```

## Stage Notes

- **Input Documents**: Source legal artifacts that enter the pipeline.
- **Extraction**: Captures relevant fields and entities from raw documents.
- **Structuring**: Normalizes extracted information into expected schemas.
- **Annotation**: Enriches structured content with labels and contextual metadata.
- **Outputs**: Persisted artifacts used for downstream review and integration.

## Prompts and Tests Relationship

- Prompts define stage behavior and quality expectations for extraction, structuring, and annotation.
- Tests provide regression coverage and confidence that each stage and output contract remains stable.
