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
    paragraph_indices: List[int] = Field(description="List of indices of the paragraphs belonging to this cluster from the input list.")

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
You are an expert legal analyst. Your task is to analyze a list of paragraphs from the same section of multiple court decisions and cluster them based on their semantic meaning.

You will be given a list of paragraphs, each with an index, title, and description.

**Instructions:**
1.  **Analyze and Cluster**: Group the paragraphs into clusters of semantically similar content. A cluster can contain one or more paragraphs.
2.  **Generate Abstract Title**: For each cluster, create a concise, abstract title that represents the core topic of the paragraphs in that cluster.
3.  **Generate Abstract Description**: For each cluster, create a list of bullet points that describe the purpose or content of the paragraphs in that cluster.
4.  **Return Indices**: For each cluster, provide the list of indices of the paragraphs that belong to it.

**Input Format:**
The input is a list of JSON objects, where each object represents a paragraph:
```json
[
  {"index": 0, "title": "Title of Para 1", "description": ["Description of Para 1"]},
  {"index": 1, "title": "Title of Para 2", "description": ["Description of Para 2"]},
  ...
]
```

**Output Format:**
Respond with a single JSON object that adheres to the following Pydantic model:
`ClusteringResult(clusters: List[ParagraphCluster])`

`ParagraphCluster(cluster_id: int, abstract_title: str, abstract_description: List[str], paragraph_indices: List[int])`
"""

def cluster_paragraphs_with_llm(
    paragraphs: List[SourceParagraph], llm: BaseChatModel
) -> ClusteringResult:
    """Clusters paragraphs using an LLM with structured output."""
    # Format the input for the LLM
    llm_input = [
        {
            "index": i,
            "title": p.annotation.title,
            "description": p.annotation.description,
        }
        for i, p in enumerate(paragraphs)
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
            # Determine if the paragraph is required
            cluster_decision_ids = {
                original_paragraphs[i].ref.decision_id for i in cluster.paragraph_indices
            }
            is_required = len(cluster_decision_ids) == total_decision_count

            # Formulate inclusion criteria for optional paragraphs
            inclusion_criteria = []
            if not is_required:
                # Simple rule based on the abstract title for this prototype
                inclusion_criteria.append(
                    f"Include if a paragraph with the topic '{cluster.abstract_title}' is present."
                )
            
            # TODO: Implement recursive processing for subparagraphs
            # For this minimal prototype, we will leave subparagraphs empty.

            template = ParagraphTemplate(
                number_pattern="X.", # Placeholder pattern
                title_template=cluster.abstract_title,
                description_template=cluster.abstract_description,
                required=is_required,
                inclusion_criteria=inclusion_criteria,
                frequency=len(cluster_decision_ids) / total_decision_count,
                similar_paragraph_refs=[
                    (1.0, original_paragraphs[i].ref) for i in cluster.paragraph_indices
                ], # Placeholder similarity
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
    llm = init_chat_model("openai:gpt-4.1-mini", temperature=0.0)
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
        annotated_decisions, section_clustering_results, aggregated_paragraphs
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