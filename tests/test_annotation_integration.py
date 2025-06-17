import pytest
import tempfile
import os
from pathlib import Path
import yaml

try:
    from src.models.extraction import (
        CourtDecision,
        MetaData,
        Section,
        Paragraph,
        ParagraphStruct,
        ParagraphStructAnnotated,
    )
    from src.annotation import (
        SectionStructured,
        CourtDecisionStructured,
        main as annotation_main,
    )
except ImportError:
    from models.extraction import (
        CourtDecision,
        MetaData,
        Section,
        Paragraph,
        ParagraphStruct,
        ParagraphStructAnnotated,
    )
    from annotation import (
        SectionStructured,
        CourtDecisionStructured,
        main as annotation_main,
    )


def create_mock_decision() -> CourtDecisionStructured:
    """Create a mock court decision with simple test data."""
    
    # Create mock metadata
    meta = MetaData(
        aktenzeichen="TEST-123/2024",
        entscheid_datum="2024-01-15",
        publikations_datum="2024-01-16",
        eingangsjahr="2024",
        abteilung="Test Abteilung",
        sprache="Deutsch",
        gegenstand="Test Fall",
        gerichtsschreiber=["Test Schreiber"],
        richter=["Test Richter"],
        parteien=["Test Partei A", "Test Partei B"],
        zitierte_gesetze=["Test Gesetz"],
        zitierte_entscheide=["Test Entscheid"],
        stichworte=["Test Stichwort"],
    )
    
    # Create mock sections with simple paragraphs
    entscheid_section = SectionStructured(
        name="entscheid",
        content=[
            Paragraph(number="1.", text="Die Beschwerde wird abgewiesen."),
            Paragraph(number="2.", text="Die Kosten werden dem Beschwerdeführer auferlegt."),
        ],
        is_structured=True
    )
    
    erwägungen_section = SectionStructured(
        name="erwägungen", 
        content=[
            Paragraph(number="1.", text="Die Beschwerde ist unbegründet."),
            Paragraph(number="2.", text="Die Kostenentscheidung ist angemessen."),
        ],
        is_structured=True
    )
    
    sachverhalt_section = SectionStructured(
        name="sachverhalt",
        content=[
            Paragraph(number="A.", text="Der Sachverhalt ist wie folgt:"),
            Paragraph(number="B.", text="Die Parteien haben folgende Positionen:"),
        ],
        is_structured=True
    )
    
    # Create the decision
    decision = CourtDecisionStructured(
        meta=meta,
        content=[entscheid_section, erwägungen_section, sachverhalt_section]
    )
    
    return decision


def create_mock_annotated_decision() -> CourtDecisionStructured:
    """Create a mock annotated decision with test annotations."""
    
    # Create mock metadata
    meta = MetaData(
        aktenzeichen="TEST-123/2024",
        entscheid_datum="2024-01-15",
        publikations_datum="2024-01-16",
        eingangsjahr="2024",
        abteilung="Test Abteilung",
        sprache="Deutsch",
        gegenstand="Test Fall",
        gerichtsschreiber=["Test Schreiber"],
        richter=["Test Richter"],
        parteien=["Test Partei A", "Test Partei B"],
        zitierte_gesetze=["Test Gesetz"],
        zitierte_entscheide=["Test Entscheid"],
        stichworte=["Test Stichwort"],
    )
    
    # Create mock annotated sections
    entscheid_section = SectionStructured(
        name="entscheid",
        content=[
            ParagraphStructAnnotated(
                number="1.",
                text="Die Beschwerde wird abgewiesen.",
                title="Abweisung der Beschwerde",
                description=["Beschwerde wird als unbegründet abgewiesen"],
                subparagraphs=[]
            ),
            ParagraphStructAnnotated(
                number="2.",
                text="Die Kosten werden dem Beschwerdeführer auferlegt.",
                title="Kostenentscheidung",
                description=["Kosten werden dem Beschwerdeführer auferlegt"],
                subparagraphs=[]
            ),
        ],
        is_structured=True
    )
    
    erwägungen_section = SectionStructured(
        name="erwägungen",
        content=[
            ParagraphStructAnnotated(
                number="1.",
                text="Die Beschwerde ist unbegründet.",
                title="Begründetheit der Beschwerde",
                description=["Prüfung der Begründetheit", "Feststellung der Unbegründetheit"],
                subparagraphs=[
                    ParagraphStructAnnotated(
                        number="1.1",
                        text="Die rechtlichen Voraussetzungen sind nicht erfüllt.",
                        title="Rechtliche Voraussetzungen",
                        description=["Prüfung der rechtlichen Voraussetzungen"],
                        subparagraphs=[]
                    )
                ]
            ),
        ],
        is_structured=True
    )
    
    sachverhalt_section = SectionStructured(
        name="sachverhalt",
        content=[
            ParagraphStructAnnotated(
                number="A.",
                text="Der Sachverhalt ist wie folgt:",
                title="Darstellung des Sachverhalts",
                description=["Beschreibung des Sachverhalts"],
                subparagraphs=[]
            ),
        ],
        is_structured=True
    )
    
    # Create the annotated decision
    decision = CourtDecisionStructured(
        meta=meta,
        content=[entscheid_section, erwägungen_section, sachverhalt_section]
    )
    
    return decision


def test_yaml_serialization_with_annotations():
    """Test that YAML serialization preserves annotations."""
    
    # Create a mock annotated decision
    decision = create_mock_annotated_decision()
    
    # Convert to YAML
    yaml_content = decision.to_yaml()
    
    # Save to temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(yaml_content)
        temp_path = f.name
    
    try:
        # Load back from YAML
        loaded_decision = CourtDecisionStructured.from_yaml_file(temp_path)
        
        # Verify that annotations are preserved
        assert len(loaded_decision.content) == 3
        
        # Check entscheid section
        entscheid = loaded_decision.content[0]
        assert entscheid.name == "entscheid"
        assert len(entscheid.content) == 2
        
        # Check first paragraph has annotations
        para1 = entscheid.content[0]
        assert para1.number == "1."
        assert para1.text == "Die Beschwerde wird abgewiesen."
        assert hasattr(para1, 'title')
        assert para1.title == "Abweisung der Beschwerde"
        assert hasattr(para1, 'description')
        assert para1.description == ["Beschwerde wird als unbegründet abgewiesen"]
        
        # Check erwägungen section has subparagraphs
        erwägungen = loaded_decision.content[1]
        assert erwägungen.name == "erwägungen"
        assert len(erwägungen.content) == 1
        
        para1_erw = erwägungen.content[0]
        assert para1_erw.number == "1."
        assert hasattr(para1_erw, 'title')
        assert para1_erw.title == "Begründetheit der Beschwerde"
        assert hasattr(para1_erw, 'subparagraphs')
        assert len(para1_erw.subparagraphs) == 1
        
        # Check subparagraph
        subpara = para1_erw.subparagraphs[0]
        assert subpara.number == "1.1"
        assert hasattr(subpara, 'title')
        assert subpara.title == "Rechtliche Voraussetzungen"
        
    finally:
        # Clean up
        os.unlink(temp_path)


def test_yaml_content_structure():
    """Test that YAML content has the expected structure with annotations."""
    
    decision = create_mock_annotated_decision()
    yaml_content = decision.to_yaml()
    
    # Check that YAML contains annotation fields
    assert "title:" in yaml_content
    assert "description:" in yaml_content
    assert "subparagraphs:" in yaml_content
    
    # Check that specific annotations are present
    assert "Abweisung der Beschwerde" in yaml_content
    assert "Begründetheit der Beschwerde" in yaml_content
    assert "Rechtliche Voraussetzungen" in yaml_content
    
    # Check that subparagraphs are present
    assert "1.1" in yaml_content


def test_model_dump_includes_annotations():
    """Test that model_dump includes all annotation fields."""
    
    decision = create_mock_annotated_decision()
    
    # Get the model dump
    dump_data = decision.model_dump(
        exclude_none=False,
        exclude_unset=False, 
        exclude_defaults=False
    )
    
    # Check that content sections have the right structure
    assert 'content' in dump_data
    assert len(dump_data['content']) == 3
    
    # Check that paragraphs have annotation fields
    for section in dump_data['content']:
        assert 'content' in section
        for para in section['content']:
            assert 'number' in para
            assert 'text' in para
            assert 'title' in para
            assert 'description' in para
            assert 'subparagraphs' in para


def create_minimal_decision_yaml(path: str):
    """Create a minimal YAML file for fast annotation workflow tests."""
    meta = MetaData(
        aktenzeichen="MIN-1/2024",
        entscheid_datum="2024-01-01",
        publikations_datum="2024-01-02",
        eingangsjahr="2024",
        abteilung="Test",
        sprache="Deutsch",
        gegenstand="Minimalfall",
        gerichtsschreiber=["A"],
        richter=["B"],
        parteien=["C"],
        zitierte_gesetze=["D"],
        zitierte_entscheide=["E"],
        stichworte=["F"],
    )
    section = Section(
        name="entscheid",
        content=[
            Paragraph(number="1.", text="Dies ist ein Testparagraph.")
        ]
    )
    decision = CourtDecision(meta=meta, content=[section])
    with open(path, "w", encoding="utf-8") as f:
        f.write(decision.to_yaml())


# If run as main, create a minimal file for manual annotation workflow
if __name__ == "__main__":
    minimal_path = "minimal_decision.yaml"
    create_minimal_decision_yaml(minimal_path)
    print(f"Minimal decision YAML written to {minimal_path}")
    # Run the tests as before
    test_yaml_serialization_with_annotations()
    test_yaml_content_structure()
    test_model_dump_includes_annotations()
    print("All tests passed!") 