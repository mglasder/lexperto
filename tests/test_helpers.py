import pytest
from pathlib import Path
import os


def test_load_items_to_examine_from_id_is_correct():
    from src.models.items import AbstrakteErwItem
    from src.utils import load_items_to_examine_from

    # Get the absolute path to the prompts directory
    base_dir = Path(__file__).parent.parent
    prompts_dir = base_dir / "prompts" / "production" / "aerw"

    items = load_items_to_examine_from(
        str(prompts_dir), item_cls=AbstrakteErwItem
    )

    ids = [item.id for item in items]
    expected_ids = [
        "aerw_001_zustaendigkeit",
        "aerw_002_anwendbares_recht",
        "aerw_007_gehoer",
    ]
    for id_ in expected_ids:
        assert id_ in ids, f"Expected ID {id_} not found in loaded items."


def test_load_yaml_to_abstrakteerwitem():
    """Test loading a YAML file into an AbstrakteErwItem instance."""
    from src.models.items import AbstrakteErwItem, SearchType
    
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
