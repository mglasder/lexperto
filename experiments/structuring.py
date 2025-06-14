from typing import Optional, List

from src.models.extraction import BaseSchema, CourtDecision, Paragraph


class ParagraphStruct(BaseSchema):
    number: Optional[str]
    text: Optional[str]
    subparagraphs: List["ParagraphStruct"] = []


def create_paragraph_struct(
    list_of_paragraphs: List[Paragraph],
) -> List[ParagraphStruct]:
    """ "
    1. loop over the paragraphs in sv
    2. for each top level paragraph (A., B., C., etc.)
        a. Create a ParagraphStruct with the number and text
        b. find the subparagraphs (A.a, A.b, etc.)
        c. insert these subparagraphs into the subparagraphs list of the top level paragraph
    3. Repeat this until the paragragraph hierarchy is exhausted
    """

    pass


def main():

    path = "../data/output/20250614_091808_schema_A-6208-2023_2025-02-28_d11ec6d4-0fe1-4cea-a1f3-cefaeee44ebf.yaml"
    decision = CourtDecision.from_yaml_file(path=path)

    sv = None
    for section in decision.sections:
        if section.name == "sachverhalt":
            sv = section

    sv_struct = create_paragraph_struct(sv.content)


if __name__ == "__main__":
    main()
