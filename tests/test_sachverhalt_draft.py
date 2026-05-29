from pathlib import Path

import pytest

from src.sachverhalt_draft import (
    build_output_path,
    build_sachverhalt_prompt,
    chat_model_init_kwargs,
    read_input_text,
    resolve_model_name,
    run_with_paths,
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


def test_chat_model_init_kwargs_omits_temperature_for_anthropic() -> None:
    assert chat_model_init_kwargs("anthropic:claude-opus-4-7") == {}
    assert chat_model_init_kwargs("openai:gpt-4.1-mini") == {"temperature": 0.3}


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


def test_run_with_paths_writes_output_file_with_mocked_dependencies(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    verfuegung_path = tmp_path / "verfuegung.txt"
    beschwerde_path = tmp_path / "beschwerde.txt"
    output_path = tmp_path / "out" / "result.txt"
    verfuegung_path.write_text("ignored", encoding="utf-8")
    beschwerde_path.write_text("ignored", encoding="utf-8")

    read_calls: list[Path] = []
    captured: dict[str, str] = {}

    def fake_read_input_text(path: Path) -> str:
        read_calls.append(path)
        if path == verfuegung_path:
            return "VERFUEGUNG CONTENT"
        if path == beschwerde_path:
            return "BESCHWERDE CONTENT"
        raise AssertionError(f"Unexpected path: {path}")

    def fake_read_optional_template(path: Path) -> str:
        return f"TEMPLATE::{path.name}"

    def fake_generate_sachverhalt(prompt: str, model_name: str) -> str:
        captured["prompt"] = prompt
        captured["model_name"] = model_name
        return "GENERATED SACHVERHALT"

    monkeypatch.setattr("src.sachverhalt_draft.read_input_text", fake_read_input_text)
    monkeypatch.setattr(
        "src.sachverhalt_draft._read_optional_template", fake_read_optional_template
    )
    monkeypatch.setattr(
        "src.sachverhalt_draft.generate_sachverhalt", fake_generate_sachverhalt
    )

    saved_path = run_with_paths(
        verfuegung_path=verfuegung_path,
        beschwerde_path=beschwerde_path,
        output_path=output_path,
        model_name="openai:gpt-4.1-mini",
    )

    assert saved_path == output_path
    assert output_path.read_text(encoding="utf-8") == "GENERATED SACHVERHALT"
    assert read_calls == [verfuegung_path, beschwerde_path]
    assert captured["model_name"] == "openai:gpt-4.1-mini"
    assert "AKTUELLE VERFÜGUNG" in captured["prompt"]
    assert "VERFUEGUNG CONTENT" in captured["prompt"]
    assert "BESCHWERDE CONTENT" in captured["prompt"]
