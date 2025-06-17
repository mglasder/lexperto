from enum import Enum
from typing import List, Optional, TYPE_CHECKING

import yaml
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from typing import ForwardRef


class BaseSchema(BaseModel):
    def to_yaml(self) -> str:
        """Convert the schema to a YAML string.

        By explicitly disabling all exclusion flags we make sure that *every* field
        – including those that are optional, have default values, or have been
        set to ``None`` – is taken over into the dictionary that is finally
        serialised.  This guarantees that annotations (``title``,
        ``description`` …) which are added programmatically after object
        creation are retained in the YAML output.
        """
        data = self.model_dump(
            exclude_none=False,  # keep fields that are ``None``
            exclude_unset=False,  # keep fields that were not explicitly set
            exclude_defaults=False,  # keep fields that equal their default value
        )

        # ``default_flow_style=False`` enforces the more readable block style
        # (instead of inline lists like ``[a, b]``) which is helpful when
        # manually inspecting the generated files.
        return yaml.dump(
            data,
            allow_unicode=True,
            sort_keys=False,
            default_flow_style=False,
        )

    def to_json(self):
        """Convert the schema to a JSON string."""
        return self.model_dump_json(indent=2, exclude_none=False, exclude_unset=False)

    @classmethod
    def from_yaml_file(cls, path: str):
        """Create an instance from a YAML dictionary."""
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return cls(**data)

    @classmethod
    def from_json_file(cls, path: str):
        """Create an instance from a JSON file."""
        with open(path, "r", encoding="utf-8") as f:
            data = f.read()
        return cls.model_validate_json(data)


class SectionName(str, Enum):
    SACHVERHALT = "sachverhalt"
    ERWAEGUNGEN = "erwaegungen"
    ENTSCHEID = "entscheid"
    RECHTSMITTEL = "rechtsmittelbelehrung"
    UNKNOWN = "unknown"


class MetaData(BaseSchema):
    aktenzeichen: Optional[str]
    entscheid_datum: Optional[str]
    publikations_datum: Optional[str]
    eingangsjahr: Optional[str]
    abteilung: Optional[str]
    sprache: Optional[str]
    gegenstand: Optional[str]
    gerichtsschreiber: List[str] = []
    richter: List[str] = []
    parteien: List[str] = []
    zitierte_gesetze: List[str] = []
    zitierte_entscheide: List[str] = []
    stichworte: List[str] = []


class AnnotationMixin(BaseSchema):
    title: str
    description: List[str] = []


class Paragraph(BaseSchema):
    number: Optional[str]
    text: Optional[str]


class ParagraphStruct(Paragraph):
    subparagraphs: List["ParagraphStruct"] = []


class ParagraphStructAnnotated(ParagraphStruct):
    """ParagraphStruct mit Annotationen des Schemas."""

    title: str = Field(
        description="Präziser und kompakter Titel für den Inhalt dieses Paragraphen und seine Unterabschnitte."
    )
    description: List[str] = Field(
        default_factory=list,
        description="Beschreibung, was in diesem Paragraphen und Subparagraphen zu prüfen ist (WAS, NICHT WIE). Jede string ist ein Stichpunkt.",
    )
    subparagraphs: List["ParagraphStructAnnotated"] = []

    class Config:
        arbitrary_types_allowed = True


class ParagraphList(BaseSchema):
    paragraphs: List[Paragraph] = []


class Section(BaseSchema):
    name: str
    content: List[Paragraph] = []


class CourtDecision(BaseSchema):
    meta: Optional[MetaData]
    content: List[Section]
