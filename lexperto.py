import os
from datetime import datetime

from agents import Agent, Runner, RunResult
from dotenv import load_dotenv
from prompts import prompt_dict
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


def create_sachverhalt(agent, prompt) -> RunResult:

    for _, p in prompt_dict.items():
        prompt.extend(p)

    prompt.extend([
        {"role": "user", "content": "Nummeriere die Absätze des Sachverhalts."},
    ])
    result = Runner.run_sync(agent, prompt)
    return result

# TODO: create document saver class
def add_to_output_word(doc: RunResult, text: RunResult) -> Document:
    result_doc = doc
    result_doc.add_heading('Urteil in Amtshilfeverfahren', level=1)
    result_doc.add_paragraph(text.final_output)
    return result_doc

def save_output_word(doc: Document, output_folder: str = "output"):
    now = datetime.now().strftime("%Y%m%d_%H%M%S")
    doc.save(f"{output_folder}/{now}_ergebnis.docx")

def main():
    agent = Agent(name="Richter", instructions=instruction, model="gpt-4.1")

    beschwerde = read_word("input/Beschwerde_Clean_Format.docx")
    verfuegung = read_word("input/Verfuegung_Clean_Format.docx")

    # TODO: create a prompt builder
    prompt = [{"role": "user", "content": "Hier ist die Verfügung:"},
             {"role": "user", "content": verfuegung},
             {"role": "user", "content": "Hier ist die Beschwerdeschrift:"},
             {"role": "user", "content": beschwerde},
             ]

    sachverhalt = create_sachverhalt(agent, prompt)

    doc = Document()
    result_doc = add_to_output_word(doc, sachverhalt)
    save_output_word(result_doc)

    # convert word document to string for output
    print("\n".join([para.text for para in result_doc.paragraphs]))

if __name__ == "__main__":
    main()