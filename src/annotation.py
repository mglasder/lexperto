import json
import os
from datetime import datetime
from typing import List, Optional, Union, Callable
import logging
import sys

from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain_core.language_models import BaseChatModel
from langgraph.constants import END
from langgraph.graph import StateGraph
from langsmith import Client
from pydantic import BaseModel, Field

from src.models.extraction import (
    Section,
    ParagraphStruct,
    ParagraphStructAnnotated,
    CourtDecision,
)
from src.structuring import create_paragraph_struct


class SectionStructured(Section):
    """A section with structured paragraphs."""

    is_structured: bool = False
    content: List[Union[ParagraphStruct, ParagraphStructAnnotated]] = []

    def structure(self):
        """Structure the section content into ParagraphStruct."""
        if not self.is_structured:
            self.content = create_paragraph_struct(self.content)
            self.is_structured = True


class CourtDecisionStructured(CourtDecision):
    """A structured court decision with annotated paragraphs."""

    content: List[Union[SectionStructured, ParagraphStructAnnotated]]

    def structure(self):
        """Structure the decision content into annotated paragraphs."""
        for section in self.content:
            section.structure()


# Basic logging setup
logging.basicConfig(
    level=logging.INFO, format="%(levelname)s: %(message)s", stream=sys.stdout
)

# Suppress pdfminer logging
logging.getLogger("pdfminer").setLevel(logging.ERROR)

load_dotenv()
os.environ["LANGSMITH_TRACING"] = "true"  # overwrites dotenv

logger = logging.getLogger(__name__)
langsmith_client = Client()

INSTRUCT_ANNOTATION = langsmith_client.pull_prompt(
    "annotate_paragraphs", include_model=False
)

CONFIG = {
    "llm_model": "openai:gpt-4.1-mini",
    "sections_in_order": ["sachverhalt", "erwägungen", "entscheid"],
}


class AnnotationState(BaseModel):
    """State for the annotation process."""

    decision: CourtDecision
    agent: Optional[Callable] = Field(None, exclude=True)

    class Config:
        arbitrary_types_allowed = True


def _annotate_paragraph_recursively(
    para: ParagraphStruct, agent: BaseChatModel, section_name: str
) -> ParagraphStructAnnotated:
    """
    Recursively annotates a paragraph and its subparagraphs using the provided agent.
    """
    context = {
        "section": section_name,
        "paragraph_number": para.number,
        "paragraph_text": para.text,
        "subparagraphs": (
            [{"number": sp.number, "text": sp.text} for sp in para.subparagraphs]
            if para.subparagraphs
            else []
        ),
    }

    logger.debug(f"Requesting annotation for paragraph {para.number}")
    response = agent.invoke(
        f"{INSTRUCT_ANNOTATION.template}\nAnnotate this paragraph from the {section_name} section:\n{context}"
    )

    try:
        response_dict = json.loads(response.content)
    except json.JSONDecodeError:
        logger.error(f"Failed to decode JSON response for paragraph {para.number}")
        # Fallback to creating an un-annotated structure
        response_dict = {"title": "Annotation Failed", "description": "JSONDecodeError"}

    logger.debug(f"Received annotation for paragraph {para.number}")
    annotated_para = ParagraphStructAnnotated(
        number=para.number,
        text=para.text,
        title=response_dict.get("title", "N/A"),
        description=response_dict.get("description", "N/A"),
        subparagraphs=[],
    )

    if para.subparagraphs:
        logger.debug(
            f"Processing {len(para.subparagraphs)} subparagraphs for {para.number}"
        )
        annotated_para.subparagraphs = [
            _annotate_paragraph_recursively(sp, agent, section_name)
            for sp in para.subparagraphs
        ]

    return annotated_para


def create_annotation_node(section_name: str):
    """Create a node that annotates paragraphs in a section."""

    def node(state: AnnotationState) -> AnnotationState:
        logger.debug(f"Entering annotation node for section: {section_name}")
        agent = state.agent

        try:
            section = next(
                s
                for s in state.decision.content
                if s.name.lower() == section_name.lower()
            )
            logger.debug(
                f"Found section '{section_name}' with {len(section.content)} paragraphs"
            )
        except StopIteration:
            logger.warning(f"Section '{section_name}' not found in decision. Skipping.")
            return state

        annotated_paragraphs = []
        for i, para in enumerate(section.content):
            logger.debug(
                f"Processing paragraph {i+1}/{len(section.content)}: {getattr(para, 'number', 'unknown')}"
            )
            if isinstance(para, ParagraphStruct):
                try:
                    annotated_para = _annotate_paragraph_recursively(
                        para, agent, section_name
                    )
                    annotated_paragraphs.append(annotated_para)
                except Exception as e:
                    logger.error(f"Error processing paragraph {para.number}: {e}")
                    # Optionally re-raise or handle to avoid stopping the whole process
                    raise
            else:
                logger.debug(f"Skipping non-ParagraphStruct content: {type(para)}")
                annotated_paragraphs.append(para)

        annotated_section = SectionStructured(
            name=section.name, content=annotated_paragraphs, is_structured=True
        )
        logger.debug(
            f"Created annotated section with {len(annotated_paragraphs)} paragraphs"
        )
        new_content = [
            s if s.name.lower() != section_name.lower() else annotated_section
            for s in state.decision.content
        ]
        new_state = state.model_copy(
            update={
                "decision": CourtDecisionStructured(
                    meta=state.decision.meta, content=new_content
                )
            }
        )
        return new_state

    return node


def build_annotation_graph(
    decision: CourtDecision, sections_in_order: List[str]
) -> StateGraph:
    """Builds the annotation graph based on sections found in the decision."""
    workflow = StateGraph(AnnotationState)
    decision_sections = {s.name.lower() for s in decision.content}

    # Determine the sequence of sections to process
    process_sequence = [s for s in sections_in_order if s in decision_sections]
    if not process_sequence:
        logger.warning("No sections to process. Graph will be empty.")
        return workflow

    logger.info(f"Processing sections in order: {process_sequence}")

    # Add nodes for each section to be processed
    for section_name in process_sequence:
        logger.info(f"Adding node for section: {section_name}")
        workflow.add_node(
            f"annotate_{section_name}", create_annotation_node(section_name)
        )

    # Set the entry point to the first section
    workflow.set_entry_point(f"annotate_{process_sequence[0]}")

    # Add edges to define the processing sequence
    for i in range(len(process_sequence) - 1):
        workflow.add_edge(
            f"annotate_{process_sequence[i]}", f"annotate_{process_sequence[i+1]}"
        )
    workflow.add_edge(f"annotate_{process_sequence[-1]}", END)

    return workflow


def main(decision: CourtDecision, debug: bool = False) -> CourtDecision:
    """Run the annotation process on a court decision.

    Args:
        decision: The court decision to annotate
        debug: Whether to enable debug logging (default: False)
    """
    if debug:
        logger.setLevel(logging.DEBUG)

    logger.info("Starting annotation process...")
    # Initialize agent
    agent = init_chat_model(CONFIG["llm_model"], temperature=0.0)
    agent.with_structured_output(ParagraphStructAnnotated)

    # Build graph
    workflow = build_annotation_graph(decision, CONFIG["sections_in_order"])
    if not workflow.nodes:
        logger.info("No nodes in the graph. Skipping execution.")
        return decision

    # Compile and run graph
    logger.info("Compiling graph...")
    graph = workflow.compile()
    input_state = AnnotationState(decision=decision, agent=agent)
    logger.info("Invoking graph...")
    result = graph.invoke(input_state)

    return result["decision"]


if __name__ == "__main__":
    logger.info("Loading decision from YAML...")
    # Load a decision from YAML
    input_path = "../data/output/20250614_113847_schema_A-6208-2023_2025-02-28_d11ec6d4-0fe1-4cea-a1f3-cefaeee44ebf.yaml"
    decision = CourtDecisionStructured.from_yaml_file(input_path)
    logger.info(f"Loaded decision with {len(decision.content)} sections")
    decision.structure()

    # Run annotation
    logger.info("Running annotation...")
    annotated_decision = main(decision, debug=True)  # Set to True for debug logging

    # Save the result
    now = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = f"../data/output/{now}_schema_A-6208-2023_2025-02-28_d11ec6d4-0fe1-4cea-a1f3-cefaeee44ebf_annotated.yaml"

    logger.info(f"Saving to {output_path}...")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(annotated_decision.to_yaml())

    logger.info("Annotation completed. Result saved to YAML file.")
