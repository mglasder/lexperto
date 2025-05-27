import os
from datetime import datetime

from agents import Agent, Runner
from dotenv import load_dotenv
from prompts import prompt_dict
from fpdf import FPDF
from docx import Document

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

instruction = """
Sie sind ein erfahrener Richter am Schweizer Bundesverwaltungsgerichts.
Formulieren Sie den Sachverhalt für ein Gerichtsurteil in einem Amtshilfeverfahren basierend auf der gegebenen 
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

agent = Agent(name="Richter", instructions=instruction, model="gpt-4.1")

def main():
    # beschwerde = read_file("data/1_beschwerde_sachverhalt.txt")
    # verfuegung = read_file("data/1_verfuegung_sachverhalt.txt")

    beschwerde = read_word("data/Beschwerde_Clean_Format.docx")
    verfuegung = read_word("data/Verfuegung_Clean_Format.docx")

    prompt = [{"role": "user", "content": "Hier ist der Sachverhalt aus der Verfügung:"},
             {"role": "user", "content": verfuegung},
             {"role": "user", "content": "Hier ist der Sachverhalt aus der Beschwerdeschrift:"},
             {"role": "user", "content": beschwerde},
             ]

    for _, p in prompt_dict.items():
        prompt.extend(p)

    prompt.extend([
        {"role": "user", "content": "Nummeriere die Absätze des Sachverhalts."},
    ])

    result = Runner.run_sync(agent, prompt)

    # timestampt as YYYYMMDD_HHMMSS
    now = datetime.now().strftime("%Y%m%d_%H%M%S")
    # save result as markdown file
    with open(f"data/{now}_ergebnis.md", "w", encoding="utf-8") as f:
        f.write(result.final_output)

    # def sanitize_text(text):
    #     return text.encode('latin-1', 'replace').decode('latin-1')  # or use 'ignore'
    #
    # # Usage before adding to PDF
    # text = sanitize_text(result.final_output)
    #
    # # save as pdf
    # pdf = FPDF()
    # pdf.add_page()
    # pdf.set_auto_page_break(auto=True, margin=15)
    # pdf.set_font("Arial", size=12)
    # for line in text.split('\n'):
    #     pdf.multi_cell(0, 10, line)
    # pdf.output(f"data/{now}_ergebnis.pdf")

    print(result.final_output)

if __name__ == "__main__":
    main()