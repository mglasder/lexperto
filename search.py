import os
from PyPDF2 import PdfReader
from agents import Runner, Agent
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

# List of DBA-CH-FR documents as (document_id, document_date, filepath, unix_timestamp)
DBA_CH_FR_DOCUMENTS = [
    (
        "A-2453-2021",
        "2023-05-03",
        "urteile/DBA-CH-FR/A-2453-2021_2023-05-03_20a30c89-9b9f-4a3e-bd6d-51981d2374ac.pdf",
        1683072000,
    ),
    (
        "A-3365-2022",
        "2024-01-05",
        "urteile/DBA-CH-FR/A-3365-2022_2024-01-05_eaa8b27a-3ebf-4ed8-aaa2-2a05355e600a.pdf",
        1704412800,
    ),
    (
        "A-3961-2022",
        "2024-04-08",
        "urteile/DBA-CH-FR/A-3961-2022_2024-04-08_1a1921c3-1aee-4a96-af47-3eb9d9867cf6.pdf",
        1712534400,
    ),
    (
        "A-4680-2021",
        "2022-08-19",
        "urteile/DBA-CH-FR/A-4680-2021_2022-08-19_ada4e85a-f69e-4f60-8fbf-8525911370ff.pdf",
        1660867200,
    ),
    (
        "A-4681-2021",
        "2022-08-19",
        "urteile/DBA-CH-FR/A-4681-2021_2022-08-19_932b40b1-701e-4c1c-b5c7-0536902f9e10.pdf",
        1660867200,
    ),
    (
        "A-4684-2021",
        "2022-08-19",
        "urteile/DBA-CH-FR/A-4684-2021_2022-08-19_624cf5d4-857b-4b5e-a759-45823aa56c9f.pdf",
        1660867200,
    ),
    (
        "A-4685-2021",
        "2022-08-19",
        "urteile/DBA-CH-FR/A-4685-2021_2022-08-19_8fb87126-b2c8-497f-be4a-da4a4b14285f.pdf",
        1660867200,
    ),
    (
        "A-4830-2021",
        "2023-10-23",
        "urteile/DBA-CH-FR/A-4830-2021_2023-10-23_9c13fc5c-089a-4835-a029-31f93416db9e.pdf",
        1698019200,
    ),
    (
        "A-5153-2023",
        "2024-11-11",
        "urteile/DBA-CH-FR/A-5153-2023_2024-11-11_f0d9086b-6def-4963-b3ec-5ff9beb6ffd0.pdf",
        1731283200,
    ),
    (
        "A-6208-2023",
        "2025-02-28",
        "urteile/DBA-CH-FR/A-6208-2023_2025-02-28_d11ec6d4-0fe1-4cea-a1f3-cefaeee44ebf.pdf",
        1740700800,
    ),
    (
        "A-4103-2022",
        "2024-04-08",
        "urteile/DBA-CH-FR/A-4103-2022_2024-04-08_f75d644b-6831-48af-a6d7-f6fe9774a529.pdf",
        1712534400,
    ),
]


from helpers import get_instr
from models.prompt import PromptBuilder

MOST_RECENT_SEARCH_AGENT = agent = Agent(
    name="MostRecentSearchAgent",
    instructions=get_instr("most_recent_search_instructions.txt"),
    model="gpt-4.1-mini",
    output_type=str,
)


def load_most_recent_ruling(folder: str = "urteile/DBA-CH-FR") -> str:
    pdf_files = DBA_CH_FR_DOCUMENTS
    pdf_files.sort(key=lambda x: x[-1], reverse=True)

    # Return the most recent file
    if pdf_files:
        path = pdf_files[0][2]
        with open(path, "rb") as file:
            # read text of pdf properly

            reader = PdfReader(file)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            # Decode the text to utf-8
            return text.strip()

    return ""


def most_recent_search(search_prompt: PromptBuilder) -> str:

    # TODO: make depending on DBA
    text = load_most_recent_ruling()

    search_prompt.add_user("Hier ist das aktuellste Urteil:")
    search_prompt.add_user(text)

    # with agent: find the paragraph relating to input in the abstragte erwägungen
    # return it word for word in plain text
    result = Runner.run_sync(MOST_RECENT_SEARCH_AGENT, search_prompt.get())

    return result.final_output


if __name__ == "__main__":

    prompt = PromptBuilder()
    prompt.add_user("Hier ist die Beschreibung des Inhalts der abstrakten Erwägung")
    prompt.add_user(
        "Prüfung, welche Informationen die Vertragsstaaten des anwendbaren DBA unter sich austauschen"
    )

    text = most_recent_search(prompt)

    # create line break every 80 characters
    formatted_text = "\n".join(text[i : i + 80] for i in range(0, len(text), 80))
    print(formatted_text)
