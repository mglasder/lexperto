import pytest
from pathlib import Path


def test_load_items_to_examine_from_id_is_correct():
    from models.items import AbstrakteErwItem
    from helpers import load_items_to_examine_from

    items = load_items_to_examine_from(
        "../prompts-test/aerw", item_cls=AbstrakteErwItem
    )

    ids = [item.id for item in items]
    expected_ids = [
        "aerw_001_zustaendigkeit",
        "aerw_002_anwendbares_recht",
        "aerw_007_gehoer",
    ]
    for id_ in expected_ids:
        assert id_ in ids, f"Expected ID {id} not found in loaded items."


def test_load_yaml_to_abstrakteerwitem():
    """Test loading a YAML file into an AbstrakteErwItem instance."""
    from models.items import AbstrakteErwItem, SearchType
    
    # Create a test YAML file
    test_yaml = """
    task: "Test task description"
    examples:
      - "Example 1"
      - "Example 2"
    mandatory: true
    requirement_for_analysis: "Test requirement"
    search: "most_recent"
    """
    
    # Write test file
    test_file = Path("test_item.yaml")
    test_file.write_text(test_yaml, encoding="utf-8")
    
    try:
        # Load the YAML into an AbstrakteErwItem
        item = AbstrakteErwItem.from_yaml(test_file)
        
        # Verify all fields are loaded correctly
        assert item.task == "Test task description"
        assert len(item.examples) == 2
        assert "Example 1" in item.examples
        assert item.mandatory is True
        assert item.requirement_for_analysis == "Test requirement"
        assert item.search == SearchType.MOST_RECENT
        
    finally:
        # Clean up
        if test_file.exists():
            test_file.unlink()
