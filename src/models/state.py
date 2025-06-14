from operator import add
from typing import TypedDict, Any
from typing_extensions import Annotated
from pydantic import Field, BaseModel


class InputState(BaseModel):
    pdf_doc: str = Field(description="Der Text des Urteils.")


class SectionTextState(BaseModel):
    sachverhalt: str = Field(description="Die Paragraphen des Sachverhalt")
    erwaegungen: str = Field(description="Die Paragraphen der Erwägungen")
    entscheid: str = Field(description="Die Paragraphen der Entscheidung")


class GraphState(TypedDict):
    sections: Annotated[list[Any], add]
