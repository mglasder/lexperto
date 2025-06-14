import pytest
from experiments.structuring import create_paragraph_struct, ParagraphStruct
from src.models.extraction import Paragraph


@pytest.mark.parametrize(
    "paragraphs,expected",
    [
        # Test case 1: Numeric numbering
        (
            [
                Paragraph(number="1", text="Introduction"),
                Paragraph(number="1.1", text="Subsection 1.1"),
                Paragraph(number="1.1.1", text="Subsection 1.1.1"),
                Paragraph(number="1.1.2", text="Subsection 1.1.2"),
                Paragraph(number="1.2", text="Subsection 1.2"),
                Paragraph(number="2", text="Conclusion"),
            ],
            [
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
            ],
        ),
        # Test case 2: Alphabetic numbering
        (
            [
                Paragraph(number="A", text="First Section"),
                Paragraph(number="A.a", text="Subsection A.a"),
                Paragraph(number="A.b", text="Subsection A.b"),
                Paragraph(number="B", text="Second Section"),
            ],
            [
                ParagraphStruct(
                    number="A",
                    text="First Section",
                    subparagraphs=[
                        ParagraphStruct(number="A.a", text="Subsection A.a", subparagraphs=[]),
                        ParagraphStruct(number="A.b", text="Subsection A.b", subparagraphs=[]),
                    ],
                ),
                ParagraphStruct(number="B", text="Second Section", subparagraphs=[]),
            ],
        ),
    ],
)
def test_create_paragraph_struct(paragraphs, expected):
    result = create_paragraph_struct(paragraphs)
    assert result == expected, f"Expected {expected}, but got {result}"
