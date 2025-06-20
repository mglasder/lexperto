import pytest
from src.structuring import create_paragraph_struct
from src.models.extraction import Paragraph, ParagraphStruct


@pytest.mark.parametrize(
    "paragraphs,expected",
    [
        # Test case 1: Numeric numbering
        (
            [
                Paragraph(number="1.", text="Introduction"),
                Paragraph(number="1.1.1.", text="Subsection 1.1.1"),
                Paragraph(number="1.1", text="Subsection 1.1"),
                Paragraph(number="2", text="Conclusion"),
                Paragraph(number="3.1", text="Subsection 3.1"),
                Paragraph(number="3.2.", text="Subsection 3.2"),
                Paragraph(number="1.1.2", text="Subsection 1.1.2"),
                Paragraph(number="1.2.", text="Subsection 1.2"),
            ],
            [
                ParagraphStruct(
                    number="1.",
                    text="Introduction",
                    subparagraphs=[
                        ParagraphStruct(
                            number="1.1",
                            text="Subsection 1.1",
                            subparagraphs=[
                                ParagraphStruct(
                                    number="1.1.1",
                                    text="Subsection 1.1.1",
                                    subparagraphs=[],
                                ),
                                ParagraphStruct(
                                    number="1.1.2",
                                    text="Subsection 1.1.2",
                                    subparagraphs=[],
                                ),
                            ],
                        ),
                        ParagraphStruct(
                            number="1.2", text="Subsection 1.2", subparagraphs=[]
                        ),
                    ],
                ),
                ParagraphStruct(number="2.", text="Conclusion", subparagraphs=[]),
                ParagraphStruct(
                    number="3.",
                    text="",
                    subparagraphs=[
                        ParagraphStruct(
                            number="3.1", text="Subsection 3.1", subparagraphs=[]
                        ),
                        ParagraphStruct(
                            number="3.2", text="Subsection 3.2", subparagraphs=[]
                        ),
                    ],
                ),
            ],
        ),
        # Test case 2: Alphabetic numbering
        (
            [
                Paragraph(number="A.", text="First Section"),
                Paragraph(number="A.a", text="Subsection A.a"),
                Paragraph(number="A.b.", text="Subsection A.b"),
                Paragraph(number="A.a.a.", text="Subsection A.a"),
                Paragraph(number="A.a.b", text="Subsection A.a"),
                Paragraph(number="B,", text="Second Section"),
            ],
            [
                ParagraphStruct(
                    number="A.",
                    text="First Section",
                    subparagraphs=[
                        ParagraphStruct(
                            number="A.a",
                            text="Subsection A.a",
                            subparagraphs=[
                                ParagraphStruct(
                                    number="A.a.a",
                                    text="Subsection A.a",
                                    subparagraphs=[],
                                ),
                                ParagraphStruct(
                                    number="A.a.b",
                                    text="Subsection A.a",
                                    subparagraphs=[],
                                ),
                            ],
                        ),
                        ParagraphStruct(
                            number="A.b", text="Subsection A.b", subparagraphs=[]
                        ),
                    ],
                ),
                ParagraphStruct(number="B.", text="Second Section", subparagraphs=[]),
            ],
        ),
        # Test case 3: Missing intermediate parents
        (
            [
                Paragraph(number="1.1.1", text="Deep child"),
                Paragraph(number="2.1", text="Second child"),
            ],
            [
                ParagraphStruct(
                    number="1.",
                    text="",
                    subparagraphs=[
                        ParagraphStruct(
                            number="1.1",
                            text="",
                            subparagraphs=[
                                ParagraphStruct(
                                    number="1.1.1",
                                    text="Deep child",
                                    subparagraphs=[],
                                ),
                            ],
                        ),
                    ],
                ),
                ParagraphStruct(
                    number="2.",
                    text="",
                    subparagraphs=[
                        ParagraphStruct(
                            number="2.1",
                            text="Second child",
                            subparagraphs=[],
                        ),
                    ],
                ),
            ],
        ),
        # Test case 4: Deep hierarchy missing multiple parents
        (
            [
                Paragraph(number="1.2.3.4", text="Deepest child"),
            ],
            [
                ParagraphStruct(
                    number="1.",
                    text="",
                    subparagraphs=[
                        ParagraphStruct(
                            number="1.2",
                            text="",
                            subparagraphs=[
                                ParagraphStruct(
                                    number="1.2.3",
                                    text="",
                                    subparagraphs=[
                                        ParagraphStruct(
                                            number="1.2.3.4",
                                            text="Deepest child",
                                            subparagraphs=[],
                                        ),
                                    ],
                                ),
                            ],
                        ),
                    ],
                ),
            ],
        ),
        # Test case 6: Multiple missing parents at different branches
        (
            [
                Paragraph(number="1.1.1", text="A child"),
                Paragraph(number="2.2.2", text="B child"),
            ],
            [
                ParagraphStruct(
                    number="1.",
                    text="",
                    subparagraphs=[
                        ParagraphStruct(
                            number="1.1",
                            text="",
                            subparagraphs=[
                                ParagraphStruct(
                                    number="1.1.1",
                                    text="A child",
                                    subparagraphs=[],
                                ),
                            ],
                        ),
                    ],
                ),
                ParagraphStruct(
                    number="2.",
                    text="",
                    subparagraphs=[
                        ParagraphStruct(
                            number="2.2",
                            text="",
                            subparagraphs=[
                                ParagraphStruct(
                                    number="2.2.2",
                                    text="B child",
                                    subparagraphs=[],
                                ),
                            ],
                        ),
                    ],
                ),
            ],
        ),
        # Test case 7: Non-sequential numbering
        (
            [
                Paragraph(number="1.", text="Top"),
                Paragraph(number="1.3", text="Third child"),
                Paragraph(number="1.3.2", text="Subchild"),
            ],
            [
                ParagraphStruct(
                    number="1.",
                    text="Top",
                    subparagraphs=[
                        ParagraphStruct(
                            number="1.3",
                            text="Third child",
                            subparagraphs=[
                                ParagraphStruct(
                                    number="1.3.2",
                                    text="Subchild",
                                    subparagraphs=[],
                                ),
                            ],
                        ),
                    ],
                ),
            ],
        ),
        # Test case 8: Already complete hierarchy
        (
            [
                Paragraph(number="1.", text="Top"),
                Paragraph(number="1.1", text="Child"),
                Paragraph(number="1.1.1", text="Grandchild"),
            ],
            [
                ParagraphStruct(
                    number="1.",
                    text="Top",
                    subparagraphs=[
                        ParagraphStruct(
                            number="1.1",
                            text="Child",
                            subparagraphs=[
                                ParagraphStruct(
                                    number="1.1.1",
                                    text="Grandchild",
                                    subparagraphs=[],
                                ),
                            ],
                        ),
                    ],
                ),
            ],
        ),
        # Test case 9: Single paragraph, already top-level
        (
            [
                Paragraph(number="1.", text="Top only"),
            ],
            [
                ParagraphStruct(
                    number="1.",
                    text="Top only",
                    subparagraphs=[],
                ),
            ],
        ),
        # Test case 10: Paragraphs with trailing commas or dots in input
        (
            [
                Paragraph(number="1,", text="Comma"),
                Paragraph(number="1.1.", text="Dot"),
                Paragraph(number="2.", text="Normal"),
            ],
            [
                ParagraphStruct(
                    number="1.",
                    text="Comma",
                    subparagraphs=[
                        ParagraphStruct(
                            number="1.1",
                            text="Dot",
                            subparagraphs=[],
                        ),
                    ],
                ),
                ParagraphStruct(
                    number="2.",
                    text="Normal",
                    subparagraphs=[],
                ),
            ],
        ),
        # Test case 11: Multiple subparagraphs under the same parent
        (
            [
                Paragraph(number="1.1", text="First"),
                Paragraph(number="1.2", text="Second"),
                Paragraph(number="1.3", text="Third"),
            ],
            [
                ParagraphStruct(
                    number="1.",
                    text="",
                    subparagraphs=[
                        ParagraphStruct(
                            number="1.1",
                            text="First",
                            subparagraphs=[],
                        ),
                        ParagraphStruct(
                            number="1.2",
                            text="Second",
                            subparagraphs=[],
                        ),
                        ParagraphStruct(
                            number="1.3",
                            text="Third",
                            subparagraphs=[],
                        ),
                    ],
                ),
            ],
        ),
        # Test case 12: Empty input
        (
            [],
            [],
        ),
    ],
)
def test_create_paragraph_struct(paragraphs, expected):
    result = create_paragraph_struct(paragraphs)
    assert result == expected, f"Expected {expected}, but got {result}"
