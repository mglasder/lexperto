import pytest


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
