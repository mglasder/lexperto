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
    if not list_of_paragraphs:
        return []

    # Sort paragraphs using the custom sort key
    sorted_paragraphs = sorted(list_of_paragraphs, key=lambda p: p.number)
    
    # Helper function to check if a paragraph is a child of another
    def is_child(child_num: str, parent_num: str) -> bool:
        if not parent_num:
            return True
        # Split by dots and compare parts
        child_parts = child_num.split('.')
        parent_parts = parent_num.split('.')
        if len(child_parts) <= len(parent_parts):
            return False
        return all(child_parts[i] == parent_parts[i] for i in range(len(parent_parts)))

    # Helper function to build the tree recursively
    def build_tree(paragraphs: List[Paragraph], parent_num: str = "") -> List[ParagraphStruct]:
        result = []
        i = 0
        while i < len(paragraphs):
            current = paragraphs[i]
            
            # Skip if this paragraph is not a direct child of the parent
            if not is_child(current.number, parent_num):
                i += 1
                continue
                
            # Find all direct children of current paragraph
            children = []
            j = i + 1
            while j < len(paragraphs) and is_child(paragraphs[j].number, current.number):
                if len(paragraphs[j].number.split('.')) == len(current.number.split('.')) + 1:
                    children.append(paragraphs[j])
                j += 1
            
            # Create the current paragraph structure with its children
            current_struct = ParagraphStruct(
                number=current.number,
                text=current.text,
                subparagraphs=build_tree(paragraphs[i+1:j], current.number)
            )
            result.append(current_struct)
            i = j
            
        return result

    return build_tree(sorted_paragraphs)


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
