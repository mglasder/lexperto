import os
import sys
from datetime import datetime

from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langgraph.constants import START, END
from langgraph.graph import StateGraph
import logging
from pathlib import Path
from typing import Optional

try:
    from langsmith import Client
except Exception:  # pragma: no cover - optional dependency at runtime
    Client = None

from models.extraction import Section, Paragraph, ParagraphList, CourtDecision
from models.state import InputState, SectionTextState, GraphState
from utils import load_pdf

# Basic logging setup
logging.basicConfig(
    level=logging.INFO, format="%(levelname)s: %(message)s", stream=sys.stdout
)

# Suppress pdfminer logging
logging.getLogger("pdfminer").setLevel(logging.ERROR)

load_dotenv()

logger = logging.getLogger(__name__)
LLM_MODEL = os.getenv("LLM_MODEL", "openai:gpt-4.1-mini")

DEFAULT_INSTRUCT_EXTRACTION = """Extrahiere aus dem folgenden Urteil die drei Abschnitte:
- Sachverhalt
- Erwägungen
- Entscheid
Gib die Abschnitte vollständig und unverändert zurück."""

DEFAULT_INSTRUCT_PARSING = """Antworte ausschließlich im folgenden strukturierten Format:
{struct}"""

DEFAULT_INSTRUCT_PARAGRAPHS = """Extrahiere alle Paragraphen für den Abschnitt "{section_name}".
Nummerierungslogik:
{numbering_logic}

Nutze für jeden Eintrag exakt diese Struktur:
{paragraph_struct}

Beispiel Input:
{example_input}

Beispiel Output:
{example_output}"""


def _resolve_prompt_from_path(path_value: Optional[str]) -> Optional[str]:
    if not path_value:
        return None
    prompt_path = Path(path_value)
    if prompt_path.exists():
        return prompt_path.read_text(encoding="utf-8")
    logger.warning("Prompt file not found at %s", prompt_path)
    return None


def _load_prompt(
    env_var_name: str, langsmith_prompt_name: str, fallback_template: str
) -> str:
    path_prompt = _resolve_prompt_from_path(os.getenv(env_var_name))
    if path_prompt:
        return path_prompt

    if Client is not None:
        try:
            langsmith_client = Client()
            prompt = langsmith_client.pull_prompt(
                langsmith_prompt_name, include_model=False
            )
            return prompt.template
        except Exception as error:
            logger.warning(
                "Falling back to local default prompt for %s: %s",
                langsmith_prompt_name,
                error,
            )

    return fallback_template


INSTRUCT_EXTRACTION = _load_prompt(
    "EXTRACTION_PROMPT_PATH", "extract_sections", DEFAULT_INSTRUCT_EXTRACTION
)
INSTRUCT_PARSING = _load_prompt(
    "PARSING_PROMPT_PATH", "structured_parsing", DEFAULT_INSTRUCT_PARSING
)
INSTRUCT_PARAGRAPHS = _load_prompt(
    "PARAGRAPHS_PROMPT_PATH", "extract_paragraphs", DEFAULT_INSTRUCT_PARAGRAPHS
)

SV_PARA_LOGIC = """
A.
A.a.
A.b.
B.a.
B.b.
C.
"""

ERW_PARA_LOGIC = """
1.
1.1.
1.2.
2.
2.1.1
2.1.2
2.2.
3.
"""


TEST_PDF_CONTENT = """

Das ist der Sachverhalt:
A.
A.a. lorem ipsum dolor sit amet, consectetur adipiscing elit.
A.b. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.
B. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.
B.a. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur.
B.b. Duis aute irure dolor in exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.
C. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Das sind die Erwägungen:
1. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.
2.
2.1 Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur.
2.2 Duis aute irure dolor in exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.
3. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.
3.1 Sed ut perspiciatis unde omnis iste natus error sit voluptatem accusantium doloremque laudantium, totam rem aperiam.
3.2 At vero eos et accusamus et iusto odio dignissimos ducimus qui blanditiis praesentium voluptatum deleniti atque corrupti.

Das ist die Entscheidung:
1. Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.
2. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.
"""


EXAMPLE_INPUT_SV = """
Das ist der Sachverhalt:
A.
A.a. lorem ipsum dolor sit amet, consectetur adipiscing elit.
A.b. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.
B. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.
B.a. Sonderzeichen, wie in Mütter, Spaß, müssen übernommen werden. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur.
B.b. Duis aute irure dolor in exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.
"""

EXAMPLE_INPUT_ERW = """
Das ist der Sachverhalt:
1.
1.1 lorem ipsum dolor sit amet, consectetur adipiscing elit.
1.2 Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.
2. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.
2.1 Sonderzeichen, wie in Mütter, Spaß, müssen übernommen werden. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur.
2.2 Duis aute irure dolor in exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.
"""

EXAMPLE_OUTPUT_SV = [
    {
        "number": "A.",
        "text": "",
    },
    {
        "number": "A.a",
        "text": "lorem ipsum dolor sit amet, consectetur adipiscing elit.",
    },
    {
        "number": "A.b",
        "text": "Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.",
    },
    {
        "number": "B.",
        "text": "Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.",
    },
    {
        "number": "B.a",
        "text": "Sonderzeichen, wie in Mütter, Spaß, müssen übernommen werden. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur.",
    },
    {
        "number": "B.b",
        "text": "Duis aute irure dolor in exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.",
    },
]

EXAMPLE_OUTPUT_ERW = [
    {
        "number": "1.",
        "text": "",
    },
    {
        "number": "1.1",
        "text": "lorem ipsum dolor sit amet, consectetur adipiscing elit.",
    },
    {
        "number": "1.2",
        "text": "Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.",
    },
    {
        "number": "2.",
        "text": "Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.",
    },
    {
        "number": "2.1",
        "text": "Sonderzeichen, wie in Mütter, Spaß, müssen übernommen werden. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur.",
    },
    {
        "number": "2.2",
        "text": "Duis aute irure dolor in exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.",
    },
]


def section_extraction_node(state: InputState) -> SectionTextState:
    logger.info("Entering section extraction node")
    openai = init_chat_model(
        LLM_MODEL,
        temperature=0.0,
    )

    agent = openai.with_structured_output(SectionTextState)

    logger.info("Invoking agent for section extraction")
    response = agent.invoke(
        f"{INSTRUCT_EXTRACTION}\n{INSTRUCT_PARSING.format(struct=SectionTextState.model_fields)}\nHier ist das Urteil: {state.pdf_doc}. Extrahiere jetzt den Sachverhalt, die Erwägungen und den Entscheid."
    )

    logger.info("Section extraction completed successfully")
    return response


def create_paragraph_extraction_node(
    section_name: str,
    content_field: str,
    numbering_logic: str,
    example_input: str,
    example_output: str,
):
    def node(state: SectionTextState) -> GraphState:
        logger.info(f"Entering paragraph extraction node for section: {section_name}")
        openai = init_chat_model(LLM_MODEL, temperature=0.0)

        agent = openai.with_structured_output(ParagraphList)

        instruct_paragraphs = INSTRUCT_PARAGRAPHS.format(
            section_name=section_name,
            numbering_logic=numbering_logic,
            paragraph_struct=Paragraph.model_fields,
            example_input=example_input,
            example_output=example_output,
        )

        instruct_parsing = INSTRUCT_PARSING.format(
            struct=ParagraphList.model_json_schema()
        )

        logger.info(f"Invoking agent for paragraph extraction in {section_name}")
        response = agent.invoke(
            f"{instruct_paragraphs}\n{instruct_parsing}\n{getattr(state, content_field)}"
        )

        section = Section(
            name=section_name.lower(),
            content=response.paragraphs,
        )
        logger.info(
            f"Created section '{section_name}' with {len(response.paragraphs)} paragraphs"
        )
        return {"sections": [section]}

    return node


paragraph_extraction_sv_node = create_paragraph_extraction_node(
    "Sachverhalt", "sachverhalt", SV_PARA_LOGIC, EXAMPLE_INPUT_SV, EXAMPLE_OUTPUT_SV
)

paragraph_extraction_erw_node = create_paragraph_extraction_node(
    "Erwägungen", "erwaegungen", ERW_PARA_LOGIC, EXAMPLE_INPUT_ERW, EXAMPLE_OUTPUT_ERW
)


def paragraph_extraction_ent_node(state: SectionTextState) -> GraphState:
    logger.info("Entering paragraph extraction node for entscheid")
    openai = init_chat_model(
        LLM_MODEL,
        temperature=0.0,
    )

    agent = openai.with_structured_output(ParagraphList)

    instruct_paragraphs = INSTRUCT_PARAGRAPHS.format(
        section_name="Entscheid",
        numbering_logic=ERW_PARA_LOGIC,
        paragraph_struct=Paragraph.model_fields,
        example_input=EXAMPLE_INPUT_ERW,
        example_output=EXAMPLE_OUTPUT_ERW,
    )

    instruct_parsing = INSTRUCT_PARSING.format(struct=ParagraphList.model_json_schema())

    logger.info("Invoking agent for entscheid paragraph extraction")
    response = agent.invoke(
        f"{instruct_paragraphs}\n{instruct_parsing}\n{state.entscheid}"
    )

    section = Section(name="entscheid", content=response.paragraphs)
    logger.info(f"Created entscheid section with {len(response.paragraphs)} paragraphs")
    return {"sections": [section]}


def combine_node(state: GraphState) -> CourtDecision:
    logger.info("Entering combine node")
    logger.info(f"Combining {len(state['sections'])} sections")

    result = CourtDecision(
        meta=None,
        content=state["sections"],
    )

    logger.info("Successfully created CourtDecision object")
    return result


def main(name: str):
    logger.info(f"Starting extraction process for: {name}")

    logger.info("Building extraction graph")
    builder = StateGraph(GraphState, input=InputState, output=CourtDecision)
    builder.add_node("section_extraction", section_extraction_node)
    builder.add_node("paragraph_extraction_sv", paragraph_extraction_sv_node)
    builder.add_node("paragraph_extraction_erw", paragraph_extraction_erw_node)
    builder.add_node("paragraph_extraction_ent", paragraph_extraction_ent_node)
    builder.add_node("combine", combine_node)

    builder.add_edge(START, "section_extraction")
    builder.add_edge("section_extraction", "paragraph_extraction_sv")
    builder.add_edge("section_extraction", "paragraph_extraction_erw")
    builder.add_edge("section_extraction", "paragraph_extraction_ent")
    builder.add_edge("paragraph_extraction_sv", "combine")
    builder.add_edge("paragraph_extraction_erw", "combine")
    builder.add_edge("paragraph_extraction_ent", "combine")
    builder.add_edge("combine", END)

    if name.lower() == "test":
        logger.info("Using test PDF content")
        pdf_doc = TEST_PDF_CONTENT
    else:
        logger.info(f"Loading PDF from file: {name}")
        pdf_doc = load_pdf(f"data/urteile/DBA-CH-FR/{name}.pdf")

    input_state = InputState(pdf_doc=pdf_doc)
    graph = builder.compile()

    logger.info("Invoking graph")
    result = graph.invoke(input_state)

    decision = CourtDecision(**result)

    logger.info("Extraction completed successfully")
    print(decision.model_dump_json(indent=2))

    now = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = f"data/schemas/extracted/{now}_schema_{name}.yaml"

    logger.info(f"Saving result to: {output_path}")
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(decision.to_yaml())

    except Exception as e:
        logger.error(f"Failed to save result to {output_path}: {e}")
        raise


if __name__ == "__main__":

    pdf_names = [
        # "A-2453-2021_2023-05-03_20a30c89-9b9f-4a3e-bd6d-51981d2374ac",
        # "A-3365-2022_2024-01-05_eaa8b27a-3ebf-4ed8-aaa2-2a05355e600a",
        # "A-3961-2022_2024-04-08_1a1921c3-1aee-4a96-af47-3eb9d9867cf6",
        # "A-4103-2022_2024-04-08_f75d644b-6831-48af-a6d7-f6fe9774a529",
        # "A-4680-2021_2022-08-19_ada4e85a-f69e-4f60-8fbf-8525911370ff",
        # "A-4681-2021_2022-08-19_932b40b1-701e-4c1c-b5c7-0536902f9e10",
        "A-4685-2021_2022-08-19_8fb87126-b2c8-497f-be4a-da4a4b14285f",
        "A-4830-2021_2023-10-23_9c13fc5c-089a-4835-a029-31f93416db9e",
        "A-5153-2023_2024-11-11_f0d9086b-6def-4963-b3ec-5ff9beb6ffd0",
    ]

    # name = "A-6208-2023_2025-02-28_d11ec6d4-0fe1-4cea-a1f3-cefaeee44ebf"

    for name in pdf_names:
        main(name)
