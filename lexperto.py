import glob
import os
from datetime import datetime
from pathlib import Path

from agents import Agent, Runner, RunResult
from dotenv import load_dotenv

from models import AbstrakteErwItem, SachverhaltItem, BasePromptItem
from docx import Document

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")


# TODO: create a detailed prompt with agentic intstructions
# TODO: externalize all prompts in text files (.txt, or simple .yaml), no complicated object creation though.

instruction = """
Sie sind ein erfahrener Richter am Schweizer Bundesverwaltungsgerichts.
Formulieren Sie den Sachverhalt für ein Gerichtsurteil in einem Amtshilfevergahren basierend auf der gegebenen 
Verfügung und Beschwerde. Verwenden Sie einen sachlichen, neutralen Stil ohne Wertungen oder Beurteilungen.
"""

def read_file(file_path):
    """Read content from a file."""
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()

def read_word(file_path):
    """Read content from a Word file."""
    doc = Document(file_path)
    return "\n".join([para.text for para in doc.paragraphs])


def create_sachverhalt(agent, prompt) -> list[str]:
    paragraphs = []


    prompt.extend([{"role": "user",
                    "content": """
                    Du wirst im folgenden den Sachverhalt für ein Gerichtsurteil in einem Amtshilfeverfahren formulieren.
                    Erstelle den Sachverhalt Paragraph für Paragraph, basierend auf der Verfügung und der Beschwerde.
                    Nutze nur die Informationen aus der Verfügung und der Beschwerde, um den Sachverhalt zu formulieren.
                    DU DARFST KEINE INFORMATIONEN HINZUFÜGEN, DIE NICHT AUS DER VERFÜGUNG ODER DER BESCHWERDE STAMMEN.
                    Du erhältst jeweils eine Beschreibung des zu erstellenden Paragraphen und ein Beispiel.
                    Sei in deiner Wortwahl so genau wie möglich und orientiere dich an den Beispielen.
                    """}])

    items = load_items_to_examine_from("prompts/sach/", item_cls=SachverhaltItem)

    for item in items:
        prompt.extend(item.task_as_prompt())
        prompt.extend(item.examples_as_prompt())
        prompt.extend([{"role": "user",
                        "content": "Erstelle jetzt den Paragraphen:"}])

        result = Runner.run_sync(agent, prompt)
        paragraphs.append(result.final_output)
        prompt = result.to_input_list()

    return paragraphs

def load_items_to_examine_from(folder : str, item_cls: BasePromptItem = AbstrakteErwItem) -> list[AbstrakteErwItem]:
    folder_path = Path(folder)
    yaml_files = glob.glob(os.path.join(folder_path, "*.yaml"))

    # sort by numbering in filename
    yaml_files.sort(key=lambda x: int(Path(x).stem.split('_')[1]))

    # exclude template files
    yaml_files = [f for f in yaml_files if "template" not in f]

    items = []

    for yaml_file in yaml_files:
        pp = item_cls.from_yaml(yaml_file)
        items.append(pp)

    return items

def create_abstract_considerations(agent, prompt) -> list[str]:

    # items of examination
    items = load_items_to_examine_from("prompts/aerw/")

    prompt.extend([{"role": "user",
                    "content": """
                    Du wirst nun den Teil des Urteils formulieren, der die abstrakten Erwägungen des Bundesverwaltungsgerichts enthält.
                    Du wirst im folgenden Prüfungspunkte zu den abstrakten Erwägungen des Bundesverwaltungsgerichts Paragraph für Paragraph bearbeiten.
                    Du erhälst zu jedem Prüfungspunkt eine Angabe, was zu Prüfen ist und ein Beispiel, wie die Prüfung formuliert werden könnte.
                    Für jeden Prüfungspunkt musst du die Beschwerde und Verfügung lesen und die relevanten Informationen für den Prüfungspunkt extrahieren.
                    Dann erstellst du einen spezifischen Absatz für den vorliegenden Fall, der sich an dem Beispiel orientiert.
                    DU DARFST NUR INFORMATIONEN AUS DER VERFÜGUNG UND DER BESCHWERDE VERWENDEN, DIE FÜR DEN PRÜFUNGSPUNKT RELEVANT SIND.
                    """,
                    }])

    results = []

    for item in items:
        prompt.extend([{"role": "user",
                        "content": "Hier ist die Angabe, was zu prüfen ist:"}])
        prompt.extend(item.task_as_prompt())

        if not item.mandatory:
            prompt.extend([{"role": "user",
                            "content": """
                            Dieser Prüfungspunkt ist nicht obligatorisch.
                            Prüfe, ob der Prüfungspunkt für den vorliegenden Fall relevant ist.
                            Hier sind die Voraussetzungen unter denen der Prüfungspunkt zu prüfen ist:
                            """
                            }])
            prompt.extend(item.requirement_as_prompt())
            prompt.extend([{"role": "user",
                            "content": "Antworte NUR mit <<Ja>> oder <<Nein>>"}])

            is_relevant = Runner.run_sync(agent, prompt)

            if is_relevant.final_output.lower() == "nein":
                continue
            else:
                prompt.extend([{"role": "user",
                                "content": "Der Prüfungspunkt ist relevant. Bitte fahre fort."}])

        prompt.extend([{"role": "user",
                        "content": "Hier ist das Beispiel, wie eine Prüfung aussehen könnte:"}])
        prompt.extend(item.examples_as_prompt())
        prompt.extend([{"role": "user",
                        "content": "Erstelle jetzt den spezifischen Absatz für den vorliegenden Fall. Gib nur den Absatz zurück, ohne sonstige Erklärungen, oder Ergänzungen."}])

        result = Runner.run_sync(agent, prompt)
        results.append(result.final_output)
        prompt = [{"role": "assistant", "content": result.final_output}]

    return results

# TODO: create document saver class
def save_output_word(doc: Document, output_folder: str = "output"):
    now = datetime.now().strftime("%Y%m%d_%H%M%S")
    doc.save(f"{output_folder}/{now}_ergebnis.docx")

def main():
    agent = Agent(name="Richter", instructions=instruction, model="gpt-4.1-mini")

    beschwerde = read_word("input/Beschwerde_Clean_Format.docx")
    verfuegung = read_word("input/Verfuegung_Clean_Format.docx")

    # TODO: create a prompt builder
    prompt = [{"role": "user", "content": "Hier ist die Verfügung:"},
             {"role": "user", "content": verfuegung},
             {"role": "user", "content": "Hier ist die Beschwerdeschrift:"},
             {"role": "user", "content": beschwerde},
             ]

    sachverhalt = create_sachverhalt(agent, prompt)

    prompt.extend([
        {"role": "user", "content": "Hier ist der vollständige Sachverhalt, den du formuliert hast:"},
    ])

    for sach in sachverhalt:
        prompt.extend([{"role": "assistant", "content": sach}])

    erwaegungen = create_abstract_considerations(agent, prompt)

    # TODO: create a document creator class
    doc = Document()
    doc.add_heading('Urteil in Amtshilfeverfahren', level=1)
    doc.add_heading('Sachverhalt:', level=2)
    for sach in sachverhalt:
        doc.add_paragraph(sach, style='List Number')
        doc.add_paragraph("")  # Add a blank line between paragraphs

    doc.add_heading('Das Bundesverwaltungsgericht zieht in Erwägungen:', level=2)
    for erw in erwaegungen:
        doc.add_paragraph(erw, style='List Number')
        doc.add_paragraph("")  # Add a blank line between paragraphs

    save_output_word(doc)

    # convert word document to string for output
    print("\n".join([para.text for para in doc.paragraphs]))

if __name__ == "__main__":
    main()