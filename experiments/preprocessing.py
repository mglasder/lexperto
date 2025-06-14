import glob

from agents import Agent, Runner
from docx import Document
from dotenv import load_dotenv
from tqdm import tqdm

from src.models.prompt import PromptBuilder

load_dotenv()

doc_agent = Agent(
    name="Document Processor Agent",
    instructions="""
    Du bist ein Dokumentenverarbeitungsagent, der PDF-Dateien liest und deren Inhalt extrahiert.
    Du extrahierst den relevanten Text und bereinigst diesen um Seitenzahlen, Kopf- und Fußzeilen sowie andere nicht relevante Informationen.
    Danach gibst du den in der bereinigten Form zurück. 
    Du teilst diesen in Paragrpahen auf, die durch eine Leerzeile getrennt sind.
    DIES IST GANZ WICHTIG. TEILE DEN TEXT MIT ZWEI LEERZEILEN IN PARAGRAPHEN AUF.
    DU MUSST DIE NUMMERIERUNG DER PARAGRAPHEN BEIBEHALTEN.
    DER TEST MUSS WORTWÖRTLICH ÜBERNOMMEN WERDEN. AUCH RECHTSCHREIB- ODER ZEICHENSETZUNGSFEHLER DÜRFEN NICHT KORRIGIERT WERDEN.
    DU DARFST KEINE INFORMATIONEN HINZUFÜGEN ODER ERFINDEN.
    """,
    model="gpt-4.1-mini",
)

if __name__ == "__main__":

    pdfs = glob.glob(f"urteile/*.pdf")

    for pdf in tqdm(pdfs):

        doc = Document()

        with open(pdf, "rb") as file:
            content = file.read()

        prompt = PromptBuilder()
        prompt.add_user("Hier ist der Content des PDF-Dokuments:")
        prompt.add_user(str(content))
        prompt.add_user("Extrahiere jetzt den Text, wie dir aufgetragen wurde.")

        result = Runner.run_sync(doc_agent, prompt.get())
        # split text at emtpy lines to create paragraphs
        paragraphs = result.final_output.split("\n\n")

        for para in paragraphs:
            doc.add_heading(para, level=1)

        # Save the document with the same name as the PDF but with .docx extension
        doc_name = pdf.replace(".pdf", ".docx")
        doc.save(doc_name)
        break
