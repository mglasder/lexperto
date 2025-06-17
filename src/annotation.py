import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional, Union
import logging
import sys

from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langgraph.constants import START, END
from langgraph.graph import StateGraph
from langsmith import Client
from pydantic import BaseModel

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

LLM_MODEL = "openai:gpt-4.1-mini"


class AnnotationState(BaseModel):
    """State for the annotation process."""

    decision: CourtDecision
    current_section: Optional[str] = None
    current_paragraph: Optional[ParagraphStruct] = None


class AnnotationResult(BaseModel):
    """Result of the annotation process."""

    annotated_paragraph: ParagraphStructAnnotated


def create_annotation_node(section_name: str):
    """Create a node that annotates paragraphs in a section."""

    def node(state: AnnotationState) -> AnnotationState:
        logger.debug(f"Entering annotation node for section: {section_name}")
        agent = init_chat_model(LLM_MODEL, temperature=0.0)
        agent.with_structured_output(ParagraphStructAnnotated)
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
            logger.error(f"Section {section_name} not found in decision")
            raise
        # agent = create_react_agent(
        #     model=openai,
        #     prompt=INSTRUCT_ANNOTATION.template,
        #     response_format=(
        #         "Parse allen Text vollständig, wortwörtlich und ohne jede Änderung",
        #         ParagraphStructAnnotated,
        #     ),
        #     tools=[],
        # )
        annotated_paragraphs = []
        for i, para in enumerate(section.content):
            logger.debug(
                f"Processing paragraph {i+1}/{len(section.content)}: {getattr(para, 'number', 'unknown')}"
            )
            if isinstance(para, ParagraphStruct):
                try:
                    context = {
                        "section": section_name,
                        "paragraph_number": para.number,
                        "paragraph_text": para.text,
                        "subparagraphs": (
                            [
                                {"number": sp.number, "text": sp.text}
                                for sp in para.subparagraphs
                            ]
                            if para.subparagraphs
                            else []
                        ),
                    }
                    logger.debug(f"Requesting annotation for paragraph {para.number}")
                    # response = agent.invoke(
                    #     {
                    #         "messages": [
                    #             {
                    #                 "role": "system",
                    #                 "content": INSTRUCT_ANNOTATION.template,
                    #             },
                    #             {
                    #                 "role": "user",
                    #                 "content": f"Annotate this paragraph from the {section_name} section:\n{context}",
                    #             },
                    #         ]
                    #     }
                    # )

                    response = agent.invoke(
                        f"{INSTRUCT_ANNOTATION.template}\nAnnotate this paragraph from the {section_name} section:\n{context}"
                    )

                    response_dict = json.loads(response.content)

                    logger.debug(f"Received annotation for paragraph {para.number}")
                    annotated_para = ParagraphStructAnnotated(
                        number=para.number,
                        text=para.text,
                        title=response_dict["title"],
                        description=response_dict["description"],
                        subparagraphs=[],
                    )
                    if para.subparagraphs:
                        logger.debug(
                            f"Processing {len(para.subparagraphs)} subparagraphs for {para.number}"
                        )
                        annotated_para.subparagraphs = [
                            process_subparagraph(sp, agent, section_name)
                            for sp in para.subparagraphs
                        ]
                    annotated_paragraphs.append(annotated_para)
                except Exception as e:
                    logger.error(f"Error processing paragraph {para.number}: {e}")
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


def process_subparagraph(
    para: ParagraphStruct, agent: Any, section_name: str
) -> ParagraphStructAnnotated:
    """Recursively process a subparagraph and its children."""
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

    # response = agent.invoke(
    #     {
    #         "messages": [
    #             {
    #                 "role": "user",
    #                 "content": f"Annotate this subparagraph from the {section_name} section:\n{context}",
    #             }
    #         ]
    #     }
    # )

    response = agent.invoke(
        f"{INSTRUCT_ANNOTATION.template}\nAnnotate this paragraph from the {section_name} section:\n{context}"
    )

    response_dict = json.loads(response.content)

    annotated_para = ParagraphStructAnnotated(
        number=para.number,
        text=para.text,
        title=response_dict["title"],
        description=response_dict["description"],
        subparagraphs=[],
    )

    if para.subparagraphs:
        annotated_para.subparagraphs = [
            process_subparagraph(sp, agent, section_name) for sp in para.subparagraphs
        ]

    return annotated_para


def main(decision: CourtDecision, debug: bool = False) -> CourtDecision:
    """Run the annotation process on a court decision.

    Args:
        decision: The court decision to annotate
        debug: Whether to enable debug logging (default: False)
    """
    if debug:
        logger.setLevel(logging.DEBUG)

    logger.info("Starting annotation process...")
    # Create the graph
    workflow = StateGraph(AnnotationState)

    # Add nodes for each section
    for section_name in ["entscheid", "erwägungen", "sachverhalt"]:
        logger.info(f"Adding node for section: {section_name}")
        workflow.add_node(
            f"annotate_{section_name}", create_annotation_node(section_name)
        )

    # Add edges
    logger.info("Adding edges...")
    workflow.add_edge("annotate_entscheid", "annotate_erwägungen")
    workflow.add_edge("annotate_erwägungen", "annotate_sachverhalt")
    workflow.add_edge("annotate_sachverhalt", END)

    # Set the entry point
    workflow.set_entry_point("annotate_entscheid")

    logger.info("Compiling graph...")
    graph = workflow.compile()
    input_state = AnnotationState(decision=decision)
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
