from pathlib import Path

import pytest

from src.sachverhalt_draft import (
    build_output_path,
    build_sachverhalt_prompt,
    read_input_text,
    resolve_model_name,
)


def test_read_input_text_supports_txt(tmp_path: Path) -> None:
    input_file = tmp_path / "verfuegung.txt"
    input_file.write_text("Verfuegung Inhalt", encoding="utf-8")

    assert "Verfuegung Inhalt" in read_input_text(input_file)


def test_read_input_text_rejects_unsupported_extension(tmp_path: Path) -> None:
    input_file = tmp_path / "verfuegung.md"
    input_file.write_text("x", encoding="utf-8")

    with pytest.raises(ValueError, match="Unsupported input format"):
        read_input_text(input_file)


def test_build_prompt_contains_required_sections() -> None:
    prompt = build_sachverhalt_prompt(
        verfuegung_text="VERFUEGUNG A",
        beschwerde_text="BESCHWERDE B",
        example_order_text="EXAMPLE ORDER",
        example_ruling_text="EXAMPLE RULING",
    )

    assert "AKTUELLE VERFÜGUNG" in prompt
    assert "DOKUMENT" in prompt
    assert "BEISPIEL VERFÜGUNG" in prompt
    assert "BEISPIEL SACHVERHALT" in prompt


def test_resolve_model_name_cli_overrides_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LLM_MODEL", "openai:gpt-4.1-mini")

    assert (
        resolve_model_name(cli_model="anthropic:claude-3-7-sonnet-latest")
        == "anthropic:claude-3-7-sonnet-latest"
    )


def test_build_output_path_uses_input_stem(tmp_path: Path) -> None:
    out = build_output_path(
        output_arg=None,
        verfuegung_path=Path("data/input/1_verfuegung_sachverhalt.txt"),
        output_dir=tmp_path,
        timestamp="20260528_123000",
    )

    assert out.name == "sachverhalt_1_verfuegung_sachverhalt_20260528_123000.txt"
