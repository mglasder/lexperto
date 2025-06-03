import os
from datetime import datetime

from agents import Agent, Runner, trace, FileSearchTool
from dotenv import load_dotenv
from helpers import (
    get_instr,
    read_word,
    load_items_to_examine_from,
    create_word_document,
)
from models.items import (
    AbstrakteErwItem,
    SachverhaltItem,
    ItemRelevanceDecision,
    SearchType,
)

from models.prompt import PromptBuilder
import logging

from models.results import RulingsResearchResult
from search import most_recent_search

logger = logging.getLogger("openai.agents.tracing")
now = datetime.now().strftime("%Y%m%d_%H%M")
logging.basicConfig(level=logging.INFO)
# logging.basicConfig(filename=f"run_logs/{now}_runlog.txt", level=logging.INFO)
logger.setLevel(logging.INFO)

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

TEST = False

if TEST:
    PROMPTS_FOLDER = "prompts-test"
else:
    PROMPTS_FOLDER = "prompts"

RICHTER_AGENT = Agent(
    name="Richter",
    instructions=get_instr("agent_instruction.txt"),
    model="gpt-4.1-mini",
)


RELEVANCE_DECIDER = Agent(
    name="Relevanzbewerter",
    instructions=get_instr("relevance_decider_instructions.txt"),
    model="gpt-4.1-mini",
    output_type=ItemRelevanceDecision,
)


RESEARCH_AGENT = agent = Agent(
    name="Rechercheassistent",
    instructions=get_instr("research_agent_instructions.txt"),
    tools=[
        FileSearchTool(
            max_num_results=15,
            vector_store_ids=["vs_683988e8fafc8191b005deb06ffac7b0"],
        ),
    ],
    output_type=str,
)


def create_sachverhalt(prompt) -> list[str]:
    paragraphs = []

    prompt.add_user(get_instr("sachv_instruction.txt"))

    items = load_items_to_examine_from(
        f"{PROMPTS_FOLDER}/sach/", item_cls=SachverhaltItem
    )

    for item in items:
        logger.info(f"Processing sachv item: {item.id}")
        prompt.add_user(item.task)
        if item.example:
            prompt.extend(item.examples_as_prompt())
        prompt.add_user("Erstelle jetzt den Paragraphen:")

        result = Runner.run_sync(RICHTER_AGENT, prompt.get())
        paragraphs.append(result.final_output)
        prompt.set_with(result.to_input_list())

    return paragraphs


def create_abstract_considerations(prompt) -> list[str]:
    prompt.add_user(get_instr("aerw_instructions.txt"))

    items: [AbstrakteErwItem] = load_items_to_examine_from(
        f"{PROMPTS_FOLDER}/aerw/", item_cls=AbstrakteErwItem
    )
    results = []

    for item in items:
        logger.info(f"Processing item: {item.id}")
        prompt.add_user("Hier ist die Angabe, was zu prüfen ist:")
        prompt.extend(item.task_as_prompt())

        if not item.mandatory:
            logger.info(f"{item.id} is not mandatory, preparing decision")
            prompt.add_user(
                """
                Dieser Prüfungspunkt ist nicht obligatorisch.
                Prüfe, ob der Prüfungspunkt für den vorliegenden Fall relevant ist und begründe dies.
                Hier sind die Voraussetzungen unter denen der Prüfungspunkt zu prüfen ist:
                """
            )
            prompt.extend(item.requirement_as_prompt())

            prompt.add_user(
                """
                Gehe wie folgt vor:
    
                1. Lese die Angabe zu dem zu prüfenden Punkt und das Beispiel sorgfältig.
                2. Lese die Voraussetzungen, die gegeben sein müssen, damit der Punkt relevant wird.
                3. Lese die Verfügung und die Beschwerde und entscheide, ob die Voraussetzung gegeben sind.
                Du darfst nur Informationen aus der Verfügung und der Beschwerde verwenden.
                DU DARFST KEINE INFORMATIONEN HINZUFÜGEN ODER ERFINDEN.
                5. Überprüfe deine Entscheidung auf Richtigkeit. Ist deine Schlussfolgerung logisch und nachvollziehbar?
                6. Gib an, ob der Prüfungspunkte relevant ist (True) oder nicht (False).
                7. Gib eine Begründung für deine Entscheidung an.
                """
            )

            decision = Runner.run_sync(RELEVANCE_DECIDER, prompt.get())

            logger.info(
                f"Decision made - {item.id} - is relevant: {decision.final_output.is_relevant}"
            )
            logger.info(
                f"Decision made - {item.id} - reason: {decision.final_output.reason}"
            )

            if not decision.final_output.is_relevant:
                continue
            else:
                prompt.add_assistant("Der Prüfungspunkt ist relevant.")
                prompt.add_assistant(decision.final_output.reason)

        prompt.add_user("Hier ist das Beispiel, wie eine Prüfung aussehen könnte:")
        prompt.extend(item.examples_as_prompt())

        # TODO: extract in a separate function
        # TODO: look for more example in old cases.
        if item.search == SearchType.MOST_RECENT:
            logger.info(f"Performing most recent search for {item.id}.")

            prompt.add_user(
                "Hier ist die aktuellste Fassung des Paragraphen zu dem zu prüfenden Punkt:"
            )
            most_recent_paragraph = most_recent_search(item.task)
            prompt.add_user(most_recent_paragraph)
            prompt.add_user(
                "Identifiziere die fallspezifischen Teile des Paragraphen, die für den vorliegenden Fall angepasst werden müssen und passe diese entsprechend an."
            )

            aligned_paragraph = Runner.run_sync(RICHTER_AGENT, prompt.get())
            prompt.set_with(aligned_paragraph.to_input_list())

        prompt.add_user("Füge den Paragraphen in das Urteil ein.")
        result = Runner.run_sync(RICHTER_AGENT, prompt.get())
        para = f"{item.id}\n" + f"{result.final_output}"
        results.append(para)
        prompt.set_with(result.to_input_list())

    return results


def main():

    with trace("Amtshilfe Workflow"):
        beschwerde = read_word("input/Beschwerde_Clean_Format.docx")
        verfuegung = read_word("input/Verfuegung_Clean_Format.docx")

        prompt = PromptBuilder()
        prompt.add_user("Hier ist die Verfügung:")
        prompt.add_user(verfuegung)
        prompt.add_user("Hier ist die Beschwerdeschrift:")
        prompt.add_user(beschwerde)

        logger.info("Starting to generate Sachverhalt...")
        sachverhalt = create_sachverhalt(prompt)
        logger.info("Sachverhalt generated.")

        prompt.add_user(
            "Hier ist der vollständige Sachverhalt, den du formuliert hast:"
        )
        for sach in sachverhalt:
            prompt.add_assistant(sach)

        logger.info("Starting to generate abstract considerations...")
        erwaegungen = create_abstract_considerations(prompt)
        logger.info("Abstract considerations generated.")

    _ = create_word_document(erwaegungen, sachverhalt, save=True, test=TEST)

    # # convert word document to string for output
    # print("\n".join([para.text for para in doc.paragraphs]))


if __name__ == "__main__":
    main()
