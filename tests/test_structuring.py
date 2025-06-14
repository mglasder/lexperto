import pytest
from experiments.structuring import create_paragraph_struct, ParagraphStruct
from src.models.extraction import Paragraph


def test_create_paragraph_struct():

    # Example paragraphs to test
    paragraphs = [
        Paragraph(number="1", text="Introduction"),
        Paragraph(number="1.1", text="Subsection 1.1"),
        Paragraph(number="1.1.1", text="Subsection 1.1.1"),
        Paragraph(number="1.1.2", text="Subsection 1.1.2"),
        Paragraph(number="1.2", text="Subsection 1.2"),
        Paragraph(number="2", text="Conclusion"),
    ]

    result = create_paragraph_struct(paragraphs)

    expected = [
        ParagraphStruct(
            number="1",
            text="Introduction",
            subparagraphs=[
                ParagraphStruct(
                    number="1.1",
                    text="Subsection 1.1",
                    subparagraphs=[
                        ParagraphStruct(
                            number="1.1.1", text="Subsection 1.1.1", subparagraphs=[]
                        ),
                        ParagraphStruct(
                            number="1.1.2", text="Subsection 1.1.2", subparagraphs=[]
                        ),
                    ],
                ),
                ParagraphStruct(number="1.2", text="Subsection 1.2", subparagraphs=[]),
            ],
        ),
        ParagraphStruct(number="2", text="Conclusion", subparagraphs=[]),
    ]

    assert result == expected, f"Expected {expected}, but got {result}"
