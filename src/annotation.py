import os
from datetime import datetime
from typing import List, Dict, Any, Optional

from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langgraph.constants import START, END
from langgraph.graph import StateGraph
from langgraph.prebuilt import create_react_agent
import logging
from langsmith import Client
from pydantic import BaseModel

from models.extraction import (
    CourtDecision,
    Section,
    ParagraphStruct,
    ParagraphStructAnnotated,
)
from models.state import GraphState
from structuring import create_paragraph_struct

logging.getLogger("pdfminer").setLevel(logging.ERROR)

load_dotenv()
os.environ["LANGSMITH_TRACING"] = "true"  # overwrites dotenv

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

    def node(state: AnnotationState) -> Dict[str, Any]:
        print(f"[DEBUG] Entering annotation node for section: {section_name}")
        openai = init_chat_model(LLM_MODEL, temperature=0.0)
        try:
            section = next(
                s
                for s in state.decision.content
                if s.name.lower() == section_name.lower()
            )
            print(
                f"[DEBUG] Found section '{section_name}' with {len(section.content)} paragraphs"
            )
        except StopIteration:
            print(f"[ERROR] Section {section_name} not found in decision")
            raise
        agent = create_react_agent(
            model=openai,
            prompt=INSTRUCT_ANNOTATION.template,
            response_format=ParagraphStructAnnotated,
            tools=[],
        )
        annotated_paragraphs = []
        for i, para in enumerate(section.content):
            print(
                f"[DEBUG] Processing paragraph {i+1}/{len(section.content)}: {getattr(para, 'number', 'unknown')}"
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
                    print(f"[DEBUG] Requesting annotation for paragraph {para.number}")
                    response = agent.invoke(
                        {
                            "messages": [
                                {
                                    "role": "user",
                                    "content": f"Annotate this paragraph from the {section_name} section:\n{context}",
                                }
                            ]
                        }
                    )
                    print(
                        f"[DEBUG] Full LLM response for paragraph {para.number}: {response}"
                    )
                    if response is None:
                        print(
                            f"[ERROR] LLM agent returned None for paragraph {para.number}"
                        )
                        raise ValueError("LLM agent returned None")
                    if "structured_response" not in response:
                        print(
                            f"[ERROR] LLM response missing 'structured_response' key: {response}"
                        )
                        raise ValueError(
                            "LLM response missing 'structured_response' key"
                        )
                    print(f"[DEBUG] Received annotation for paragraph {para.number}")
                    annotated_para = ParagraphStructAnnotated(
                        number=para.number,
                        text=para.text,
                        title=response["structured_response"].title,
                        description=response["structured_response"].description,
                        subparagraphs=[],
                    )
                    if para.subparagraphs:
                        print(
                            f"[DEBUG] Processing {len(para.subparagraphs)} subparagraphs for {para.number}"
                        )
                        annotated_para.subparagraphs = [
                            process_subparagraph(sp, agent, section_name)
                            for sp in para.subparagraphs
                        ]
                    annotated_paragraphs.append(annotated_para)
                except Exception as e:
                    print(f"[ERROR] Error processing paragraph {para.number}: {e}")
                    raise
            else:
                print(f"[DEBUG] Skipping non-ParagraphStruct content: {type(para)}")
                annotated_paragraphs.append(para)
        annotated_section = Section(name=section.name, content=annotated_paragraphs)
        print(
            f"[DEBUG] Created annotated section with {len(annotated_paragraphs)} paragraphs"
        )
        new_content = [
            s if s.name.lower() != section_name.lower() else annotated_section
            for s in state.decision.content
        ]
        result = {
            "decision": CourtDecision(meta=state.decision.meta, content=new_content)
        }
        new_state = state.model_copy(
            update={
                "decision": CourtDecision(meta=state.decision.meta, content=new_content)
            }
        )
        print(
            f"[DEBUG] Returning from annotation node for section: {section_name} -> {type(new_state)}"
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

    response = agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": f"Annotate this subparagraph from the {section_name} section:\n{context}",
                }
            ]
        }
    )

    annotated_para = ParagraphStructAnnotated(
        number=para.number,
        text=para.text,
        title=response["structured_response"].title,
        description=response["structured_response"].description,
        subparagraphs=[],
    )

    if para.subparagraphs:
        annotated_para.subparagraphs = [
            process_subparagraph(sp, agent, section_name) for sp in para.subparagraphs
        ]

    return annotated_para


def main(decision: CourtDecision) -> CourtDecision:
    print("\nRunning annotation...")
    print("Starting annotation process...")

    # Debug print to show input decision structure
    print("\n[DEBUG] Input decision structure:")
    print(f"Decision type: {type(decision)}")
    print(f"Decision attributes: {dir(decision)}")
    print(f"Type of decision.content: {type(decision.content)}")
    print(
        f"Value of decision.content: {repr(decision.content)[:500]}"
    )  # Print up to 500 chars
    # Comment out the for-loop for now to avoid errors
    # for section_name, section in decision.sections.items():
    #     print(f"\nSection '{section_name}' type: {type(section)}")
    #     print(f"Number of paragraphs: {len(section.paragraphs)}")
    #     if section.paragraphs:
    #         first_para = section.paragraphs[0]
    #         print(f"First paragraph type: {type(first_para)}")
    #         print(f"First paragraph content: {first_para.content[:100]}...")  # Show first 100 chars

    # Create the graph
    workflow = StateGraph(AnnotationState)

    # Add nodes for each section
    print("Adding nodes for each section...")
    for section_name in ["entscheid", "erwägungen", "sachverhalt"]:
        print(f"Adding node for section: {section_name}")
        workflow.add_node(
            f"annotate_{section_name}", create_annotation_node(section_name)
        )

    # Add edges
    print("Adding edges...")
    workflow.add_edge("annotate_entscheid", "annotate_erwägungen")
    print("Connecting annotate_entscheid to annotate_erwägungen")
    workflow.add_edge("annotate_erwägungen", "annotate_sachverhalt")
    print("Connecting annotate_erwägungen to annotate_sachverhalt")
    workflow.add_edge("annotate_sachverhalt", END)
    print("Connecting annotate_sachverhalt to END")

    # Set the entry point
    workflow.set_entry_point("annotate_entscheid")

    print("Compiling graph...")
    graph = workflow.compile()
    print("Creating input state...")
    input_state = AnnotationState(decision=decision)
    print("Invoking graph...")
    result = graph.invoke(input_state)
    print(f"Graph result type: {type(result)}")
    print(f"Graph result: {result}")

    return result["decision"]


if __name__ == "__main__":
    print("Loading decision from YAML...")
    # Load a decision from YAML
    input_path = "../data/output/20250614_113847_schema_A-6208-2023_2025-02-28_d11ec6d4-0fe1-4cea-a1f3-cefaeee44ebf.yaml"
    decision = CourtDecision.from_yaml_file(input_path)
    print(f"Loaded decision with {len(decision.content)} sections")

    # # Convert all section paragraphs to ParagraphStruct
    # struct_sections = []
    # for section in decision.content:
    #     para_struct = create_paragraph_struct(section.content)
    #     # Take only first 2 paragraphs from each section for faster testing
    #     test_paras = para_struct[:1]
    #     struct_sections.append(Section(name=section.name, content=test_paras))
    # decision_struct = decision.model_copy(deep=True)
    # decision_struct.content = struct_sections

    # Run annotation
    print("Running annotation...")
    annotated_decision = main(decision_struct)
    print(f"Annotation result type: {type(annotated_decision)}")
    print(f"Annotation result: {annotated_decision}")

    # Save the result
    now = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = f"../data/output/{now}_schema_A-6208-2023_2025-02-28_d11ec6d4-0fe1-4cea-a1f3-cefaeee44ebf_annotated.yaml"

    print(f"Saving to {output_path}...")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(annotated_decision.to_yaml())

    print("Annotation completed. Result saved to YAML file.")
