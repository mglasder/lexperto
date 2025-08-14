import yaml
from datetime import datetime
from typing import List, Tuple, Dict, Union
from pydantic import Field
import sys
import os
from collections import defaultdict
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain_core.language_models import BaseChatModel
import json

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


# --- LLM-based Aggregation and Clustering ---

from src.models.extraction import ParagraphAnnotation, ParagraphStruct

# Set up environment for LangChain/LangSmith
load_dotenv()
os.environ["LANGSMITH_TRACING"] = "false"

# -- Pydantic Models for LLM Interaction --

class ParagraphCluster(BaseSchema):
    """Represents a cluster of semantically similar paragraphs as identified by the LLM."""
    cluster_id: int = Field(description="A unique ID for this cluster.")
    abstract_title: str = Field(description="A concise, abstract title for the paragraph cluster.")
    abstract_description: List[str] = Field(description="A list of bullet points for the abstract description.")
    paragraph_indices: List[str] = Field(description="List of refs of the paragraphs belonging to this cluster from the input list.")

class ClusteringResult(BaseSchema):
    """The structured result of clustering paragraphs for a single section."""
    clusters: List[ParagraphCluster]

# -- Data Aggregation Logic --

class SourceParagraph(BaseSchema):
    """A helper class to hold a paragraph and its source reference for processing."""
    ref: SourceParagraphRef
    text: str
    annotation: ParagraphAnnotation
    subparagraphs: List["SourceParagraph"] = []


def aggregate_paragraphs_by_section(
    decisions: List[CourtDecisionStructured],
) -> Dict[str, List[SourceParagraph]]:
    """Aggregates all paragraphs from a list of decisions, grouped by section name."""
    aggregated = defaultdict(list)

    def process_paragraphs_recursively(
        paragraphs: List[Union[ParagraphStructAnnotated, ParagraphStruct]], decision_id: str, section_name: str
    ) -> List[SourceParagraph]:
        """Recursively processes paragraphs and their subparagraphs."""
        source_paragraphs = []
        for p in paragraphs:
            # Ensure we only process structured paragraphs with annotations
            if not isinstance(p, ParagraphStructAnnotated):
                continue

            ref = SourceParagraphRef(
                decision_id=decision_id,
                section=section_name,
                paragraph_number=p.number,
            )
            sub_source_paragraphs = []
            if p.subparagraphs:
                sub_source_paragraphs = process_paragraphs_recursively(
                    p.subparagraphs, decision_id, section_name
                )
            
            # Ensure annotation is not None before creating SourceParagraph
            if p.annotation:
                source_p = SourceParagraph(
                    ref=ref,
                    text=p.text,
                    annotation=p.annotation,
                    subparagraphs=sub_source_paragraphs,
                )
                source_paragraphs.append(source_p)
        return source_paragraphs

    for decision in decisions:
        decision_id = getattr(decision.meta, 'aktenzeichen', 'unknown_decision')
        for section in decision.content:
            if isinstance(section, (SectionStructured, Section)) and hasattr(section, 'content'):
                source_paras = process_paragraphs_recursively(
                    section.content, decision_id, section.name
                )
                aggregated[section.name].extend(source_paras)

    return aggregated


# -- LLM-based Clustering Logic --

CLUSTER_PROMPT = """
Sie sind ein erfahrener Rechtsanalytiker. Ihre Aufgabe ist es, eine Liste von Absätzen aus demselben Abschnitt mehrerer Gerichtsentscheidungen zu analysieren und sie basierend auf ihrer semantischen Bedeutung zu gruppieren.

Ihnen wird eine Liste von Absätzen vorgelegt, jeder mit einem Index, einem Titel und einer Beschreibung.

**Anweisungen:**
1.  **Analysieren und Gruppieren**: Gruppieren Sie die Absätze in Cluster von semantisch ähnlichem Inhalt. Ein Cluster kann einen oder mehrere Absätze enthalten.
2.  **Abstrakten Titel generieren**: Erstellen Sie für jeden Cluster einen prägnanten, abstrakten Titel, der das Kernthema der Absätze in diesem Cluster repräsentiert.
3.  **Abstrakte Beschreibung generieren**: Erstellen Sie für jeden Cluster eine Liste von Aufzählungspunkten, die den Zweck oder Inhalt der Absätze in diesem Cluster beschreiben.
4.  **Indizes zurückgeben**: Geben Sie für jeden Cluster die Liste der Indizes der Absätze zurück, die zu ihm gehören.

**Eingabeformat:**
Die Eingabe ist eine Liste von JSON-Objekten, wobei jedes Objekt einen Absatz repräsentiert:
```json
[
  {"index": 0, "title": "Titel von Absatz 1", "description": ["Beschreibung von Absatz 1"]},
  {"index": 1, "title": "Titel von Absatz 2", "description": ["Beschreibung von Absatz 2"]},
  ...
]
```

**Ausgabeformat:**
Antworten Sie mit einem einzelnen JSON-Objekt, das dem folgenden Pydantic-Modell entspricht:
`ClusteringResult(clusters: List[ParagraphCluster])`

`ParagraphCluster(cluster_id: int, abstract_title: str, abstract_description: List[str], paragraph_indices: List[str])`
"""

def cluster_paragraphs_with_llm(
    paragraphs: List[SourceParagraph], llm: BaseChatModel
) -> ClusteringResult:
    """Clusters paragraphs using an LLM with structured output."""
    # Format the input for the LLM
    llm_input = [
        {
            "index": p.ref.paragraph_number,
            "title": p.annotation.title,
            "description": p.annotation.description,
        }
        for p in paragraphs
    ]

    # Create the LLM chain with structured output
    structured_llm = llm.with_structured_output(ClusteringResult)

    # Invoke the LLM
    print(f"\nSending {len(llm_input)} paragraphs to LLM for clustering...")
    result = structured_llm.invoke(
        [
            ("system", CLUSTER_PROMPT),
            ("human", f"Here are the paragraphs to cluster:\n{json.dumps(llm_input, indent=2)}"),
        ]
    )
    print("LLM clustering complete.")
    return result


# --- Master Schema Assembly ---

def create_master_schema(
    all_decisions: List[CourtDecisionStructured],
    section_clustering_results: Dict[str, ClusteringResult],
    aggregated_paragraphs_by_section: Dict[str, List[SourceParagraph]],
    llm: BaseChatModel
) -> MasterSchema:
    """Assembles the final MasterSchema from the clustering results."""
    master_sections = []
    total_decision_count = len(all_decisions)
    decision_ids = [getattr(d.meta, 'aktenzeichen', 'N/A') for d in all_decisions]

    # Define the order of sections
    section_order = {"sachverhalt": 0, "erwägungen": 1, "entscheid": 2}

    for section_name, clustering_result in section_clustering_results.items():
        paragraph_templates = []
        original_paragraphs = aggregated_paragraphs_by_section[section_name]

        for cluster in clustering_result.clusters:
            # All paragraphs are required
            # TODO: implement
            is_required = determine_requirement_dummy()

            # Get the decision IDs where this cluster appears
            # The LLM returns string indices, so we need to find the actual paragraphs
            cluster_decision_ids = set()
            for idx in cluster.paragraph_indices:
                # Find paragraphs with matching paragraph_number
                for para in original_paragraphs:
                    if para.ref.paragraph_number == idx:
                        cluster_decision_ids.add(para.ref.decision_id)
                        break

            # Recursively process subparagraphs for arbitrary depth using LLM
            subparagraph_templates = []
            for idx in cluster.paragraph_indices:
                source_paragraph = original_paragraphs[idx]
                if source_paragraph.subparagraphs:
                    sub_templates = process_subparagraphs_recursively(
                        source_paragraph.subparagraphs, 
                        total_decision_count,
                        original_paragraphs,
                        llm
                    )
                    subparagraph_templates.extend(sub_templates)

            template = ParagraphTemplate(
                number_pattern="X.", # Placeholder pattern
                title_template=cluster.abstract_title,
                description_template=cluster.abstract_description,
                required=is_required,
                inclusion_criteria=[],
                frequency=len(cluster_decision_ids) / total_decision_count,
                similar_paragraph_refs=[
                    (1.0, original_paragraphs[i].ref) for i in cluster.paragraph_indices
                ], # Placeholder similarity
                subparagraph_templates=subparagraph_templates,
            )
            paragraph_templates.append(template)

        master_section = MasterSection(
            name=section_name,
            order=section_order.get(section_name, 99),
            paragraph_templates=paragraph_templates,
        )
        master_sections.append(master_section)

    # Sort sections by predefined order
    master_sections.sort(key=lambda s: s.order)

    master_schema = MasterSchema(
        legal_type="Administrative Court Decision",
        version="0.1.0",
        created_date=datetime.now(),
        last_updated=datetime.now(),
        source_decisions=decision_ids,
        sections=master_sections,
    )

    return master_schema


def process_subparagraphs_recursively(
    subparagraphs: List[SourceParagraph], 
    total_decision_count: int,
    all_paragraphs: List[SourceParagraph],
    llm: BaseChatModel
) -> List[ParagraphTemplate]:
    """Recursively processes subparagraphs to arbitrary depth using LLM for similarity."""
    if not subparagraphs:
        return []
    
    # Group similar subparagraphs by their annotation content using LLM
    subparagraph_groups = group_similar_subparagraphs(subparagraphs, llm)
    
    templates = []
    for group in subparagraph_groups:
        # All subparagraphs are required
        is_required = determine_requirement_dummy()
        
        # Get the decision IDs where this group appears
        group_decision_ids = {sp.ref.decision_id for sp in group}
        
        # Recursively process deeper levels
        deeper_subparagraphs = []
        for sp in group:
            if sp.subparagraphs:
                deeper_templates = process_subparagraphs_recursively(
                    sp.subparagraphs, 
                    total_decision_count,
                    all_paragraphs,
                    llm
                )
                deeper_subparagraphs.extend(deeper_templates)
        
        # Create template for this group
        template = ParagraphTemplate(
            number_pattern="X.X", # Placeholder pattern for subparagraphs
            title_template=group[0].annotation.title,
            description_template=group[0].annotation.description,
            required=is_required,
            inclusion_criteria=[],
            frequency=len(group_decision_ids) / total_decision_count,
            similar_paragraph_refs=[(1.0, sp.ref) for sp in group],
            subparagraph_templates=deeper_subparagraphs,
        )
        templates.append(template)
    
    return templates


def group_similar_subparagraphs(subparagraphs: List[SourceParagraph], llm: BaseChatModel) -> List[List[SourceParagraph]]:
    """Groups subparagraphs by similarity in their annotation content using LLM."""
    if not subparagraphs:
        return []
    
    # LLM-based similarity grouping for intelligent categorization
    # In a production system, this could use more sophisticated similarity algorithms
    groups = []
    processed = set()
    
    for i, sp in enumerate(subparagraphs):
        if i in processed:
            continue
            
        current_group = [sp]
        processed.add(i)
        
        # Find similar subparagraphs using LLM
        for j, other_sp in enumerate(subparagraphs[i+1:], i+1):
            if j in processed:
                continue
                
            if are_subparagraphs_similar(sp, other_sp, llm):
                current_group.append(other_sp)
                processed.add(j)
        
        groups.append(current_group)
    
    return groups


def are_subparagraphs_similar(sp1: SourceParagraph, sp2: SourceParagraph, llm: BaseChatModel) -> bool:
    """Determines if two subparagraphs are similar enough to group together using LLM."""
    
    # Create a prompt for the LLM to assess similarity
    similarity_prompt = f"""
    Du bist ein Experte für rechtliche Dokumentenanalyse. Deine Aufgabe ist es zu beurteilen, ob zwei Absätze semantisch ähnlich genug sind, um sie in der gleichen Gruppe zu kategorisieren.

    **Absatz 1:**
    - Titel: {sp1.annotation.title}
    - Beschreibung: {', '.join(sp1.annotation.description)}
    - Text: {sp1.text}

    **Absatz 2:**
    - Titel: {sp2.annotation.title}
    - Beschreibung: {', '.join(sp2.annotation.description)}
    - Text: {sp2.text}

    **Frage:** Sind diese beiden Absätze semantisch ähnlich genug, um sie in der gleichen Kategorie zu gruppieren?

    **Antwort:** Antworte nur mit "JA" oder "NEIN".
    """

    try:
        # Get LLM response
        response = llm.invoke([
            ("system", "Du bist ein Experte für rechtliche Dokumentenanalyse. Antworte nur mit JA oder NEIN."),
            ("human", similarity_prompt)
        ])
        
        # Parse the response
        response_text = response.content.strip().upper()
        return response_text in ["JA", "YES", "J", "Y"]
        
    except Exception as e:
        print(f"LLM similarity check failed, falling back to simple matching: {e}")
        # Fallback to simple similarity if LLM fails
        title_similar = (sp1.annotation.title == sp2.annotation.title or
                        sp1.annotation.title.lower() == sp2.annotation.title.lower())
        
        desc1 = " ".join(sp1.annotation.description).lower()
        desc2 = " ".join(sp2.annotation.description).lower()
        desc_similar = desc1 == desc2 or desc1 in desc2 or desc2 in desc1
        
        return title_similar and desc_similar


def determine_requirement_dummy() -> bool:
    """Dummy function that always returns True (required)."""
    return True


if __name__ == "__main__":
    # Define the directory containing the fake annotated schemas
    fake_data_dir = "data/schemas/fake_annotated"

    # Load the fake decisions
    annotated_decisions = load_annotated_decisions(fake_data_dir)

    print(f"Successfully loaded {len(annotated_decisions)} fake annotated decisions.")
    for decision in annotated_decisions:
        # Use a null-safe way to access aktenzeichen
        aktenzeichen = getattr(decision.meta, 'aktenzeichen', 'N/A')
        print(f"  - {aktenzeichen}")

    # Aggregate paragraphs by section
    aggregated_paragraphs = aggregate_paragraphs_by_section(annotated_decisions)

    print("\nAggregated Paragraphs by Section:")
    for section_name, paragraphs in aggregated_paragraphs.items():
        print(f"  - Section '{section_name}': {len(paragraphs)} paragraphs")

    # Initialize the LLM
    # As per the plan, we use a real LLM. This follows the pattern in annotation.py
    llm = init_chat_model("openai:gpt-5-mini")
    print("\nLLM initialized successfully.")

    # Store clustering results for each section
    section_clustering_results = {}

    # Process each section
    for section_name, paragraphs in aggregated_paragraphs.items():
        if not paragraphs:
            print(f"\nSkipping section '{section_name}' as it has no paragraphs.")
            continue

        print(f"\n--- Processing Section: {section_name} ---")
        clustering_result = cluster_paragraphs_with_llm(paragraphs, llm)
        section_clustering_results[section_name] = clustering_result

        # Print the results for verification
        print(f"\nClustering Results for Section: {section_name}")
        for cluster in clustering_result.clusters:
            print(f"  - Cluster ID: {cluster.cluster_id}")
            print(f"    - Abstract Title: {cluster.abstract_title}")
            print(f"    - Paragraph Indices: {cluster.paragraph_indices}")

    # Assemble the master schema
    print("\n--- Assembling Master Schema ---")
    master_schema = create_master_schema(
        annotated_decisions, section_clustering_results, aggregated_paragraphs, llm
    )
    print("Master schema assembled successfully.")

    # Save the master schema to a YAML file
    output_dir = "data/output/master_schemas"
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f"master_schema_{datetime.now().strftime('%Y%m%d_%H%M%S')}.yaml")
    
    # The `to_yaml` method is inherited from `BaseSchema` in `src.models.extraction`
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(master_schema.to_yaml())
        
    print(f"\nMaster schema saved to: {output_path}") 