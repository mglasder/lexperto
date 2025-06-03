import asyncio
import json
from typing import List

from agents import function_tool, Runner, Agent, FileSearchTool, ModelSettings, trace
from dotenv import load_dotenv
from pydantic import BaseModel

from helpers import get_instr, load_prompt, read_word
from lexperto import create_sachverhalt
from models.prompt import PromptBuilder

load_dotenv()

VS_ID = "vs_683b3ac457b08191a6097bf4542ad2e3"


class SectionAgentInput(BaseModel):
    section: str
    user_question: str
    guidance: str


class ExaminationItem(BaseModel):
    title: str
    description: str
    mandatory: bool


class SchemaOutput(BaseModel):
    schmema: List[ExaminationItem]


def build_para_search_tool():
    return Agent(
        name="Paragraphen-Suchwerkzeug",
        instructions=load_prompt("multi/para-search.md"),
        tools=[
            FileSearchTool(
                vector_store_ids=[VS_ID],
                include_search_results=True,
            ),
        ],
        model="gpt-4.1-mini",
        model_settings=ModelSettings(parallel_tool_calls=True, temperature=0),
    )


def build_schema_agent():
    return Agent(
        name="Urteilsanalyst Prüfungsschema",
        instructions=load_prompt("multi/schema.md"),
        tools=[
            FileSearchTool(
                vector_store_ids=[VS_ID],
                include_search_results=True,
            ),
        ],
        model="gpt-4.1-mini",
        model_settings=ModelSettings(parallel_tool_calls=True, temperature=0),
        output_type=str,
    )


@function_tool(
    name_override="sachverhalt_explizit",
    description_override="Erstellt den Sachverhalt explizit",
)
def build_sachverhalt_explicit_tool(input: SectionAgentInput):

    prompt = PromptBuilder()
    prompt.add_user(input.user_question)
    prompt.add_user(input.guidance)

    return create_sachverhalt(prompt)


def build_sachverhalt_agent(para_search_tool):
    return Agent(
        name="Gerichtsschreiber Sachverhalt",
        instructions=load_prompt("multi/sachv.md"),
        model="gpt-4.1-mini",
        output_type=str,
        tools=[
            para_search_tool.as_tool(
                tool_name="Paragraphen-Recherche-Assistent",
                tool_description="Recherchiere relevante Paragraphen aus alten Urteilen für den Sachverhalt und gibt diese wortwörtliche wieder.",
            )
        ],
        model_settings=ModelSettings(parallel_tool_calls=True, temperature=0),
    )


def build_aerw_agent(para_search_tool):
    return Agent(
        name="Gerichtsschreiber Abstrakte Erwägungen",
        instructions=load_prompt("multi/aerw.md"),
        model="gpt-4.1-mini",
        output_type=str,
        tools=[
            para_search_tool.as_tool(
                tool_name="Paragraphen-Recherche-Assistent",
                tool_description="Recherchiere relevante Paragraphen aus alten Urteilen für die Abstrakten Erwägungen und gibt diese wortwörtliche wieder.",
            )
        ],
        model_settings=ModelSettings(parallel_tool_calls=True, temperature=0),
    )


async def section_analysis_func(agent, input: SectionAgentInput):
    result = await Runner.run(
        starting_agent=agent,
        input=json.dumps(input.model_dump()),
        max_turns=75,
    )
    return result.final_output


async def run_section_agents_parallel(
    sachv_agent,
    abstrerw_agent,
    sv_input: SectionAgentInput,
    aerw_input: SectionAgentInput,
):
    result = await asyncio.gather(
        section_analysis_func(sachv_agent, sv_input),
        section_analysis_func(abstrerw_agent, aerw_input),
    )
    return {
        "sachv": result[0],
        "aerw": result[1],
    }


def build_head_judge_agent(schema_agent, sachv_agent, abstrerw_agent):
    def make_agent_tool(agent, name, description):
        @function_tool(name_override=name, description_override=description)
        async def agent_tool(input: SectionAgentInput):
            return await section_analysis_func(agent, input)

        return agent_tool

    schema_tool = make_agent_tool(
        schema_agent,
        "schema_analysis",
        "Analysiere das Prüfungsschema für einen Abschnitt eines Urteils.",
    )

    sachv_tool_exlicit = build_sachverhalt_explicit_tool

    aerw_tool = make_agent_tool(
        abstrerw_agent,
        "aerw_analysis",
        "Erstelle den Abschnitt zu den abstrakten Erwägungen.",
    )

    @function_tool(
        name_override="run_section_agents_parallel",
        description_override="Führe die Analysen des Sachverhalts-Agenten und des Abstrakte-Erwägungen-Agenten parallel aus.",
    )
    async def run_all_section_agents_tool(
        sachv_input: SectionAgentInput, aerw_input: SectionAgentInput
    ):
        return await run_section_agents_parallel(
            sachv_agent, abstrerw_agent, sachv_input, aerw_input
        )

    return Agent(
        name="Senior Richter",
        instructions=load_prompt("multi/richter.md"),
        tools=[schema_tool, sachv_tool_exlicit, aerw_tool],
        model="gpt-4.1-mini",
        model_settings=ModelSettings(temperature=0, parallel_tool_calls=True),
    )


async def run_workflow():

    prompt = PromptBuilder()
    prompt.add_user(
        "Erstelle das Sachverhalt und die Abstrakten Erwägungen für den folgenden Fall:"
    )
    prompt.add_user("Hier ist die Beschwerde:")
    beschwerde = read_word("input/Beschwerde_Clean_Format.docx")
    prompt.add_user(beschwerde)
    prompt.add_user("Hier ist die Verfügung:")
    verfuegung = read_word("input/Verfuegung_Clean_Format.docx")
    prompt.add_user(verfuegung)

    schema_agent = build_schema_agent()
    # sachverhalt_agent = build_sachverhalt_agent(build_para_search_tool())
    abstrerw_agent = build_aerw_agent(build_para_search_tool())

    richter = build_head_judge_agent(schema_agent, None, abstrerw_agent)

    with trace(
        "Amtshilfe Multi-Agent Workflow",
    ) as workflow_trace:

        response = None
        try:
            response = await asyncio.wait_for(
                Runner.run(richter, prompt.get(), max_turns=40), timeout=1200
            )
        except asyncio.TimeoutError:
            print("\n❌ Workflow timed out after 20 minutes.")

        try:
            output = response.final_output
            print(f"Output: {output}")
        except Exception as e:
            print(f"Could not parse and print output: {e}")


if __name__ == "__main__":
    asyncio.run(run_workflow())
