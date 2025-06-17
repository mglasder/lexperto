import os
from datetime import datetime

from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langgraph.constants import START, END
from langgraph.graph import StateGraph
from langgraph.prebuilt import create_react_agent
import logging
from langsmith import Client

from models.extraction import Section, Paragraph, ParagraphList
from src.structuring import CourtDecision
from models.state import InputState, SectionTextState, GraphState
from utils import load_pdf

logging.getLogger("pdfminer").setLevel(logging.ERROR)

load_dotenv()
os.environ["LANGSMITH_TRACING"] = "true"  # overwrites dotenv


langsmith_client = Client()

INSTRUCT_EXTRACTION = langsmith_client.pull_prompt(
    "extract_sections", include_model=False
)
INSTRUCT_PARSING = langsmith_client.pull_prompt(
    "structured_parsing", include_model=False
)
INSTRUCT_PARAGRAPHS = langsmith_client.pull_prompt(
    "extract_paragraphs", include_model=False
)

LLM_MODEL = "openai:gpt-4.1-mini"

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
    openai = init_chat_model(
        LLM_MODEL,
        temperature=0.0,
    )

    agent = create_react_agent(
        model=openai,
        prompt=INSTRUCT_EXTRACTION.template,
        response_format=(
            INSTRUCT_PARSING.format(struct=SectionTextState.model_fields),
            SectionTextState,
        ),
        tools=[],
    )

    response = agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": f"Hier ist das Urteil: {state.pdf_doc}. Extrahiere jetzt den Sachverhalt, die Erwägungen und den Entscheid.",
                }
            ]
        }
    )

    return response["structured_response"]


def create_paragraph_extraction_node(
    section_name: str,
    content_field: str,
    numbering_logic: str,
    example_input: str,
    example_output: str,
):
    def node(state: SectionTextState) -> GraphState:
        openai = init_chat_model(LLM_MODEL, temperature=0.0)

        agent = create_react_agent(
            model=openai,
            prompt=INSTRUCT_PARAGRAPHS.format(
                section_name=section_name,
                numbering_logic=numbering_logic,
                paragraph_struct=Paragraph.model_fields,
                example_input=example_input,
                example_output=example_output,
            ),
            response_format=(
                INSTRUCT_PARSING.format(struct=ParagraphList.model_json_schema()),
                ParagraphList,
            ),
            tools=[],
        )

        response = agent.invoke(
            {"messages": [{"role": "user", "content": getattr(state, content_field)}]}
        )

        section = Section(
            name=section_name.lower(),
            content=response["structured_response"].paragraphs,
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
    openai = init_chat_model(
        LLM_MODEL,
        temperature=0.0,
    )

    agent = create_react_agent(
        model=openai,
        prompt=INSTRUCT_PARAGRAPHS.format(
            section_name="Entscheid",
            numbering_logic=ERW_PARA_LOGIC,
            paragraph_struct=Paragraph.model_fields,
            example_input=EXAMPLE_INPUT_ERW,
            example_output=EXAMPLE_OUTPUT_ERW,
        ),
        response_format=(
            INSTRUCT_PARSING.format(struct=ParagraphList.model_json_schema()),
            ParagraphList,
        ),
        tools=[],
    )

    response = agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": state.entscheid,
                }
            ]
        }
    )

    section = Section(
        name="entscheid", content=response["structured_response"].paragraphs
    )
    return {"sections": [section]}


def combine_node(state: GraphState) -> CourtDecision:
    return CourtDecision(
        meta=None,
        content=state["sections"],
    )


def main(name: str):

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
        pdf_doc = TEST_PDF_CONTENT
    else:
        pdf_doc = load_pdf(name)

    input_state = InputState(pdf_doc=pdf_doc)
    graph = builder.compile()
    result = graph.invoke(input_state)

    decision = CourtDecision(**result)

    print(decision.model_dump_json(indent=2))

    now = datetime.now().strftime("%Y%m%d_%H%M%S")

    with open(f"../data/output/{now}_schema_{name}.yaml", "w", encoding="utf-8") as f:
        f.write(decision.to_yaml())


if __name__ == "__main__":

    # pdf_names = [
    #     # "A-2453-2021_2023-05-03_20a30c89-9b9f-4a3e-bd6d-51981d2374ac",
    #     # "A-3365-2022_2024-01-05_eaa8b27a-3ebf-4ed8-aaa2-2a05355e600a",
    #     # "A-3961-2022_2024-04-08_1a1921c3-1aee-4a96-af47-3eb9d9867cf6",
    #     # "A-4103-2022_2024-04-08_f75d644b-6831-48af-a6d7-f6fe9774a529",
    #     # "A-4680-2021_2022-08-19_ada4e85a-f69e-4f60-8fbf-8525911370ff",
    #     # "A-4681-2021_2022-08-19_932b40b1-701e-4c1c-b5c7-0536902f9e10",
    #     "A-4685-2021_2022-08-19_8fb87126-b2c8-497f-be4a-da4a4b14285f",
    #     "A-4830-2021_2023-10-23_9c13fc5c-089a-4835-a029-31f93416db9e",
    #     "A-5153-2023_2024-11-11_f0d9086b-6def-4963-b3ec-5ff9beb6ffd0",
    # ]

    # for name in pdf_names:
    #     print(f"Processing {name}...")
    #     main(name)
    #     print(f"Finished processing {name}.\n")
    name = "A-6208-2023_2025-02-28_d11ec6d4-0fe1-4cea-a1f3-cefaeee44ebf"
    name = "test"
    main(name)
