from enum import Enum
from typing import List, Optional, Union

import yaml
from pydantic import BaseModel, Field


class BaseSchema(BaseModel):
    def to_yaml(self) -> str:
        """Convert the schema to a YAML string."""
        return yaml.dump(self.model_dump(), allow_unicode=True, sort_keys=False)

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


class ParagraphStruct(BaseSchema):
    number: Optional[str]
    text: Optional[str]
    subparagraphs: List["ParagraphStruct"] = []


class ParagraphList(BaseSchema):
    paragraphs: List[Paragraph] = []


class Section(BaseSchema):
    name: str
    content: List[Union[Paragraph, ParagraphStruct]] = []


class CourtDecision(BaseSchema):
    meta: Optional[MetaData]
    content: List[Section]
