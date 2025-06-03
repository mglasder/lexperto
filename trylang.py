from datetime import datetime
import os
from typing import Optional, List, Tuple

from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langgraph.prebuilt import create_react_agent
import pdfplumber
from pydantic import BaseModel, Field

from helpers import load_prompt

import logging

logging.getLogger("pdfminer").setLevel(logging.ERROR)

load_dotenv()
os.environ["LANGSMITH_TRACING"] = "true"  # overwrites dotenv


class ExaminationItem(BaseModel):
    title: str = Field(
        description="Ein konziser und präziser Titel des zu prüfenden Punktes."
    )
    description: List[str] = Field(
        description="Liste mit Beschreibungen des zu prüfenen Punktes. Jeder str ist eine Stichpunkt."
    )
    example: str = Field(
        description="Wortwörtliches, typisches Beispiel aus einem Urteil. Ein ganzer Paragrpah."
    )
    reference: str = Field(
        description="Ein Verweis auf das Urteil. Format: Urteil, Paragraph."
    )

    # class Config:
    #     arbitrary_types_allowed = True


class Schema(BaseModel):
    items: list[ExaminationItem] = Field(
        description="Eine Liste von Punkten, die geprüft werden müssen"
    )


class AgentResponse(BaseModel):
    response: Schema
    debug_info: Optional[str] = Field(
        None,
        description="Gib hier Debug-Informationen an, wenn du die Aufgabe nicht erfüllen kannst.",
    )


PDF_LIST = """

- A-2453-2021_2023-05-03_20a30c89-9b9f-4a3e-bd6d-51981d2374ac
- A-3365-2022_2024-01-05_eaa8b27a-3ebf-4ed8-aaa2-2a05355e600a
- A-3961-2022_2024-04-08_1a1921c3-1aee-4a96-af47-3eb9d9867cf6
- A-4103-2022_2024-04-08_f75d644b-6831-48af-a6d7-f6fe9774a529
- A-4680-2021_2022-08-19_ada4e85a-f69e-4f60-8fbf-8525911370ff
- A-4681-2021_2022-08-19_932b40b1-701e-4c1c-b5c7-0536902f9e10
- A-4684-2021_2022-08-19_624cf5d4-857b-4b5e-a759-45823aa56c9f
- A-4685-2021_2022-08-19_8fb87126-b2c8-497f-be4a-da4a4b14285f
- A-4830-2021_2023-10-23_9c13fc5c-089a-4835-a029-31f93416db9e
- A-5153-2023_2024-11-11_f0d9086b-6def-4963-b3ec-5ff9beb6ffd0
- A-6208-2023_2025-02-28_d11ec6d4-0fe1-4cea-a1f3-cefaeee44ebf
"""


def main():
    def load_pdf(name: str) -> str:
        """Load a PDF file as text.

        Args:
            name (str): The name of the PDF file without extension.
        Returns:
            str: The text content of the PDF file.
        """

        with pdfplumber.open(f"urteile/DBA-CH-FR/{name}.pdf") as pdf:
            full_text = ""
            for page in pdf.pages:
                # Extract text from each page, preserving line breaks
                text = page.extract_text()
                if text:
                    full_text += text + "\n\n"

        return full_text

    INSTRUCTIONS = load_prompt("multi/schema_no_steps.md")

    openai = init_chat_model(
        "openai:gpt-4.1-mini",
        temperature=0.0,
    )

    # anthropic = init_chat_model(
    #     "anthropic:claude-4",
    #     temperature=0.0,
    # )

    agent = create_react_agent(
        model=openai,
        tools=[load_pdf],
        prompt=INSTRUCTIONS + PDF_LIST,
    )

    # Run the agent
    response = agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": "Erstelle jetzt ein Schema für die abstrakten Erwägungen in Amtshilfeurteilen.",
                }
            ]
        }
    )

    print(response["messages"][-1].content)
    # save as markdown file
    now = datetime.now().strftime("%Y%m%d_%H%M%S")
    with open(f"output/{now}_schema_aerw.md", "w", encoding="utf-8") as f:
        f.write(response["messages"][-1].content)


if __name__ == "__main__":
    main()
