from typing import List, Union
from src.models.extraction import Paragraph, Section, ParagraphStruct, CourtDecision, ParagraphStructAnnotated


def clean_paragraph_number(number: str) -> str:
    """Clean paragraph number according to rules:
    - Top level paragraphs must end with a dot (e.g., "1.", "A.")
    - Lower level paragraphs must not end with a dot (e.g., "1.1", "A.a")
    """
    # Remove any trailing dots and commas
    number = number.rstrip(".,")

    # If it's a top level paragraph (no dots in the middle), add a dot at the end
    if "." not in number[:-1]:  # Check if there are no dots except possibly at the end
        return number + "."
    return number


def get_level(number: str) -> int:
    """
    Helper: get the level of a paragraph (number of dots, top-level has 1 dot at the end)
    """
    # Remove trailing dot for counting
    return (
        number.rstrip(".").count(".") + 1
        if number.endswith(".")
        else number.count(".") + 1
    )


def add_missing_top_levels(paragraphs: List[Paragraph]) -> List[Paragraph]:
    """Add missing parent paragraphs for any subparagraphs without parents at any level."""
    existing_numbers = {p.number for p in paragraphs}
    to_add = set()
    # Collect all parent numbers that are missing
    for p in paragraphs:
        # Clean up the number for consistent parent detection
        number = p.number.rstrip(".,")
        parts = number.split(".")
        for i in range(1, len(parts)):
            parent = ".".join(parts[:i])
            # Top-level parent should end with a dot
            if i == 1:
                parent_number = parent + "."
            else:
                parent_number = parent
            if parent_number not in existing_numbers:
                to_add.add(parent_number)
    # Add missing parents with empty text
    for number in to_add:
        paragraphs.append(Paragraph(number=number, text=""))
    # If we added any, we need to check again recursively (in case of multi-level missing)
    if to_add:
        return add_missing_top_levels(paragraphs)
    return paragraphs


def create_paragraph_struct(
    list_of_paragraphs: List[Paragraph],
) -> List[ParagraphStruct]:
    """
    1. loop over the paragraphs in sv
    2. for each top level paragraph (A., B., C., etc.)
        a. Create a ParagraphStruct with the number and text
        b. find the subparagraphs (A.a, A.b, etc.)
        c. insert these subparagraphs into the subparagraphs list of the top level paragraph
    3. Repeat this until the paragragraph hierarchy is exhausted
    """
    if not list_of_paragraphs:
        return []

    # Clean paragraph numbers
    cleaned_paragraphs = [
        Paragraph(number=clean_paragraph_number(p.number), text=p.text)
        for p in list_of_paragraphs
    ]

    # Add missing top-level paragraphs for subparagraphs without parents
    cleaned_paragraphs = add_missing_top_levels(cleaned_paragraphs)

    # Sort paragraphs using the cleaned numbers
    sorted_paragraphs = sorted(cleaned_paragraphs, key=lambda p: p.number)

    # Recursive function to build the tree
    def build_tree(paragraphs, parent_level=1, parent_number=None):
        result = []
        paragraph_idx = 0
        while paragraph_idx < len(paragraphs):
            paragraph = paragraphs[paragraph_idx]
            paragraph_level = get_level(paragraph.number)
            # If we're at the expected level (top-level or sub-level)
            if (parent_level == 1 and paragraph.number.endswith(".")) or (
                parent_level > 1 and not paragraph.number.endswith(".")
            ):
                # Find all children (next level deeper)
                child_paragraphs = []
                child_idx = paragraph_idx + 1
                while (
                    child_idx < len(paragraphs)
                    and get_level(paragraphs[child_idx].number) > paragraph_level
                ):
                    child_paragraphs.append(paragraphs[child_idx])
                    child_idx += 1
                # Recursively build children
                struct = ParagraphStruct(
                    number=paragraph.number,
                    text=paragraph.text,
                    subparagraphs=build_tree(
                        child_paragraphs,
                        parent_level=paragraph_level + 1,
                        parent_number=paragraph.number,
                    ),
                )
                result.append(struct)
                paragraph_idx = child_idx
            else:
                paragraph_idx += 1
        return result

    return build_tree(sorted_paragraphs, parent_level=1)


class SectionStructured(Section):
    """A section with structured paragraphs."""

    is_structured: bool = False
    content: List[Union[ParagraphStruct, ParagraphStructAnnotated]] = []

    # def structure(self):
    #     """Structure the section content into ParagraphStruct."""
    #     if not self.is_structured:
    #         self.content = create_paragraph_struct(self.content)
    #         self.is_structured = True


class CourtDecisionStructured(CourtDecision):
    """A structured court decision with annotated paragraphs."""

    content: List[Union[Section, SectionStructured]]

    def structure(self):
        """Structure the decision content into annotated paragraphs."""
        new_content = []
        for section in self.content:
            if isinstance(section, SectionStructured) and not section.is_structured:
                section.structure()
                new_content.append(section)
            elif isinstance(section, Section):
                # Convert Section to SectionStructured using the new function
                structured_section = create_section_struct(section)
                new_content.append(structured_section)
            else:
                new_content.append(section)
        self.content = new_content


def create_section_struct(section: Section) -> SectionStructured:
    """
    Convert a Section to SectionStructured by converting its content from Paragraph to ParagraphStruct.
    
    Args:
        section: The Section to convert
        
    Returns:
        SectionStructured with structured content
    """
    structured_content = create_paragraph_struct(section.content)
    return SectionStructured(
        name=section.name,
        content=structured_content,
        is_structured=True
    )


def main():

    path = "../data/output/20250614_113847_schema_A-6208-2023_2025-02-28_d11ec6d4-0fe1-4cea-a1f3-cefaeee44ebf.yaml"
    decision = CourtDecision.from_yaml_file(path=path)

    sections = []
    for section in decision.content:
        para_struct = create_paragraph_struct(section.content)
        sections.append(Section(name=section.name, content=para_struct))

    decision_struct = decision.model_copy(deep=True)
    decision_struct.content = sections

    print(decision)


if __name__ == "__main__":
    main()
