import random
import string
from typing import List

from agents import Agent, FileSearchTool, Runner, ModelSettings
from dotenv import load_dotenv
from openai import OpenAI
from openai.types import Reasoning
from pydantic import BaseModel, Field
from tqdm import tqdm

from helpers import get_instr
from models.prompt import PromptBuilder

load_dotenv()

client = OpenAI()


class ExaminationItem(BaseModel):
    title: str = Field(..., description="Kurzer, präziser Titel des Prüfungspunktes")
    description: str = Field(
        ...,
        description="Präzise und ausführliche Beschreibung des Inhalts des Prüfungspunktes. Was ist zu prüfen, nicht wie?",
    )
    mandatory: bool = Field(
        ...,
        description="Obligatorisch (True) oder fakultativ (False). Ein obligatorischer Punkt muss in allen Urteilen vorkommen, ein fakultativer Punkt nur in manchen.",
    )


class SchemaOutput(BaseModel):
    schmema: List[ExaminationItem]


def main():
    VS_ID = (
        "vs_683b3ac457b08191a6097bf4542ad2e3"  # "vs_683b1c81357c819184c4e28ddf3d34ed"
    )

    path_to_files = "urteile/DBA-CH-FR"
    filenames = [
        "A-4685-2021_2022-08-19_8fb87126-b2c8-497f-be4a-da4a4b14285f.pdf",
        "A-4830-2021_2023-10-23_9c13fc5c-089a-4835-a029-31f93416db9e.pdf",
        "A-5153-2023_2024-11-11_f0d9086b-6def-4963-b3ec-5ff9beb6ffd0.pdf",
        "A-6208-2023_2025-02-28_d11ec6d4-0fe1-4cea-a1f3-cefaeee44ebf.pdf",
        "A-4680-2021_2022-08-19_ada4e85a-f69e-4f60-8fbf-8525911370ff.pdf",
        "A-4681-2021_2022-08-19_932b40b1-701e-4c1c-b5c7-0536902f9e10.pdf",
        "A-4684-2021_2022-08-19_624cf5d4-857b-4b5e-a759-45823aa56c9f.pdf",
        "A-4685-2021_2022-08-19_8fb87126-b2c8-497f-be4a-da4a4b14285f.pdf",
        "A-4830-2021_2023-10-23_9c13fc5c-089a-4835-a029-31f93416db9e.pdf",
        "A-5153-2023_2024-11-11_f0d9086b-6def-4963-b3ec-5ff9beb6ffd0.pdf",
        "A-6208-2023_2025-02-28_d11ec6d4-0fe1-4cea-a1f3-cefaeee44ebf.pdf",
    ]

    if not VS_ID:
        # create 4 char random string lowercase
        uuid = "".join(random.choices(string.ascii_lowercase, k=4))
        name = f"Amtshilfe-DBA-{uuid}"
        vectorstore = client.vector_stores.create(name=name)
        VS_ID = vectorstore.id
        print(VS_ID)

        for f in tqdm(filenames):
            file_path = f"{path_to_files}/{f}"
            _ = client.vector_stores.file_batches.upload_and_poll(
                vector_store_id=VS_ID,
                files=[open(file_path, "rb")],
            )

    agent = Agent(
        name="HierarchieErsteller",
        instructions=get_instr("hierarchy_creation_instructions.txt"),
        model="gpt-4.1-mini",
        output_type=str,
        tools=[
            FileSearchTool(
                vector_store_ids=[VS_ID],
                include_search_results=True,
            ),
        ],
        model_settings=ModelSettings(temperature=0.1),
    )

    schema_parser = Agent(
        name="SchemaParser",
        instructions="Du überführst die Inputbeschreibung des Prüfungsschemas in eine eindeutiges Schema von Prüfungspunkten.",
        model="gpt-4.1-mini",
        output_type=SchemaOutput,
        model_settings=ModelSettings(temperature=0),
    )

    result = Runner.run_sync(agent, "Lese jetzt alle Urteile im Vectorstore.")

    # "Die Hierarchie MUSS mindestens 2 Ebenen (1., 1.1., 1.2., ...) und DARF bis zu 3 Ebenen (1. , 1.1., 1.1.1, 1.1.2, ...) tief sein, wenn notwendig."

    prompt = result.to_input_list()
    prompt.extend(
        [
            {
                "content": """
Erstelle eine vollständinge Prüfungshierarchie für die abstrakten Erwägungen, in der alle zu prüfenden Punkte enthalten sind. 
Abstrakte Erwägungen sind ausschließlich solche, in denen grundsätzliche rechtliche Aspekte beschrieben werden. 
Eine Subsumtion findet nicht statt. 
 
Die Hierarchie MUSS 2 Ebenen (1., 1.1., 1.2., ...) haben.

DENKE DABEI IN PARAGRAPHEN, in der Regel entspricht 
ein Prüfungspunkt einem Paragraphen. Markiere ob Prüfungspunkte fakultativ sind oder obligatorisch. 
Die Hierarchie MUSS vollständig sein, alle jemals enthaltenen Punkte aus alten Urteilen müssen abgebildet werden.
LIES dazu ALLE Urteile im Vektorstore.

Gehe wie folgt vor:

1. Suche aus ALLEN Urteilen ALLE Prüfungspunkte NUR zu ABSTRAKTEN ERWÄGUNGEN heraus.
2. Erstelle eine Liste mit ALLEN PRÜFUNGSPUNKTE als ALLEN URTEILEN, streiche DOPPLUNGEN heraus.
3. Markiere Prüfungspunkte als OBLIGATORISCH (O) oder als FAKULTATIV (F).

Erläuterungen zum Vorgehen:
1. Gehe alle Urteile durch und extrahiere alla Prüfungspunkte. Denk in Paragraphen. Nimm immer GANZE Paragraphen als Grundlage für einen Prüfungspunkt. Zerteile Paragraphen NICHT in mehrere Prüfungspunkte. Gib jedem Prüfungspunkt eine präzise Bezeichnung.
Formuliere die Bezeichnung so, dass sie die Essenz des Prüfungspunkt trifft. Achte auf die korrekte Reihenfolge der Prüfungspunkte.
2. Erstelle so eine Liste mit allen Prüfungspunkte. Wenn du einen Prüfungspunkt hinzufügst, prüfe, ob dieser schon existiert. Lege keine Dopplungen an.
Achte darauf, das die Reihenfolge der Prüfungspunkte der Reihenfolge in den Urteilen entspricht.
3. Markiere solche Punkte, die immer in allen Urteilen vorgkommen als obligatorisch (O), und solche die nur manchmal geprüft werden als fakultativ (F). Auch Unterpunkte müssen markeirt werden.

Erstelle jetzt die Hierarchie
""",
                "role": "user",
            }
        ]
    )

    result = Runner.run_sync(agent, prompt)
    prompt = result.to_input_list()
    prompt.extend(
        [
            {
                "content": "Überprüfe nochmals alle Prüfungspunkte ob sie obligatorisch (O) oder fakultativ (F) sind."
                "Obligatorisch ist ein Punkt, wenn es in ALLEN alten Urteilen einen Paragraphen zu diesem Punkt gibt."
                "Faklutative ist ein Punkt, wenn es NICHT in ALLEN alten Urteilen, sondern nur in manchen einen entsprechenden Paragraphen gibt."
                "Ändere AUF KEINEN FALL die generierte Prüfungshierarchy. DIESE MUSS WORTWÖRTLICH ÜBERNOMMEN WERDEN."
                "Gib diese Hierarchy mit den richtigen Markierungen in obligatorisch/ fakultativ aus.",
                "role": "user",
            }
        ]
    )

    result = Runner.run_sync(agent, prompt)

    schema = Runner.run_sync(schema_parser, result.to_input_list())

    content = schema.final_output
    # formatted_text = "\n".join(
    #     content[i : i + 100] for i in range(0, len(content), 100)
    # )
    # print(formatted_text)
    print(content)


if __name__ == "__main__":
    main()
