import argparse
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

load_dotenv()

DEFAULT_MODEL = "openai:gpt-4.1-mini"
DEFAULT_OUTPUT_DIR = Path("data/output")
EXAMPLE_ORDER_PATH = Path("data/templates/court_order_sample.txt")
EXAMPLE_RULING_PATH = Path("data/templates/factual_section_example.txt")


def read_input_text(input_path: Path) -> str:
    if not input_path.exists():
        raise RuntimeError(f"Input file does not exist: {input_path}")

    suffix = input_path.suffix.lower()
    if suffix == ".txt":
        return input_path.read_text(encoding="utf-8")
    if suffix == ".docx":
        try:
            from docx import Document
        except ImportError as error:
            raise RuntimeError(
                "python-docx is required to read .docx files. Install it with "
                "`pixi add python-docx` (then `pixi install`) or use a .txt input."
            ) from error

        document = Document(input_path)
        return "\n".join(paragraph.text for paragraph in document.paragraphs).strip()
    raise ValueError(f"Unsupported input format: {input_path.suffix}")


def build_sachverhalt_prompt(
    verfuegung_text: str,
    beschwerde_text: Optional[str],
    example_order_text: Optional[str],
    example_ruling_text: Optional[str],
) -> str:
    prompt = (
        "Du bist ein erfahrener Richter am deutschen Amtsgericht. "
        "Formuliere den Sachverhalt für ein Urteil basierend auf der gegebenen Verfügung. "
        "Verwende einen sachlichen, neutralen Stil ohne Wertungen oder Beurteilungen."
    )

    if example_order_text and example_ruling_text:
        prompt += (
            f"\n\nBEISPIEL VERFÜGUNG:\n{example_order_text}\n\n"
            f"BEISPIEL SACHVERHALT:\n{example_ruling_text}\n\n---\n"
        )

    prompt += f"\nAKTUELLE VERFÜGUNG:\n{verfuegung_text}\n"
    if beschwerde_text:
        prompt += f"\nDOKUMENT:\n{beschwerde_text}\n"
    prompt += (
        '\nVerfasse nun einen Sachverhalt für diese Verfügung. '
        'Beginne mit "SACHVERHALT" und beschränke dich auf die relevanten Fakten.'
    )
    return prompt


def resolve_model_name(cli_model: Optional[str]) -> str:
    if cli_model:
        return cli_model
    draft_model = os.getenv("SACHVERHALT_DRAFT_MODEL")
    if draft_model:
        return draft_model
    return os.getenv("LLM_MODEL", DEFAULT_MODEL)


def build_output_path(
    output_arg: Optional[str], verfuegung_path: Path, output_dir: Path, timestamp: str
) -> Path:
    if output_arg:
        output_path = Path(output_arg)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        return output_path

    output_dir.mkdir(parents=True, exist_ok=True)
    output_filename = f"sachverhalt_{verfuegung_path.stem}_{timestamp}.txt"
    return output_dir / output_filename


def validate_provider_credentials(model_name: str) -> None:
    if model_name.startswith("openai:") and not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY is required for openai:* models")
    if model_name.startswith("anthropic:") and not os.getenv("ANTHROPIC_API_KEY"):
        raise RuntimeError("ANTHROPIC_API_KEY is required for anthropic:* models")


def generate_sachverhalt(prompt: str, model_name: str) -> str:
    try:
        from langchain.chat_models import init_chat_model

        validate_provider_credentials(model_name)
        model = init_chat_model(model_name, temperature=0.3)
        response = model.invoke(prompt)
        content = getattr(response, "content", "")
        if not isinstance(content, str) or not content.strip():
            raise RuntimeError("Model returned empty content")
        return content.strip()
    except Exception as error:
        raise RuntimeError(
            f"Failed to generate Sachverhalt with model '{model_name}' during model invocation."
        ) from error


def _read_optional_input(path: Optional[Path]) -> Optional[str]:
    if path is None:
        return None
    text = read_input_text(path)
    if not text.strip():
        raise RuntimeError(
            f"Optional beschwerde input is empty: {path}. Provide non-empty content or omit --beschwerde."
        )
    return text


def _read_required_input(path: Path) -> str:
    text = read_input_text(path)
    if not text.strip():
        raise RuntimeError(
            f"Required verfuegung input is empty: {path}. Provide a non-empty file for --verfuegung."
        )
    return text


def _read_optional_template(path: Path) -> Optional[str]:
    if not path.exists():
        return None
    return path.read_text(encoding="utf-8")


def run_with_paths(
    verfuegung_path: Path,
    beschwerde_path: Optional[Path],
    output_path: Path,
    model_name: str,
) -> Path:
    verfuegung_text = _read_required_input(verfuegung_path)
    beschwerde_text = _read_optional_input(beschwerde_path)
    example_order_text = _read_optional_template(EXAMPLE_ORDER_PATH)
    example_ruling_text = _read_optional_template(EXAMPLE_RULING_PATH)

    prompt = build_sachverhalt_prompt(
        verfuegung_text=verfuegung_text,
        beschwerde_text=beschwerde_text,
        example_order_text=example_order_text,
        example_ruling_text=example_ruling_text,
    )
    output_text = generate_sachverhalt(prompt=prompt, model_name=model_name)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(output_text, encoding="utf-8")
    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a Sachverhalt draft.")
    parser.add_argument("--verfuegung", required=True, help="Path to ruling input file.")
    parser.add_argument("--beschwerde", help="Optional path to complaint input file.")
    parser.add_argument("--output", help="Optional output file path.")
    parser.add_argument("--model", help="Optional model override, e.g. openai:gpt-4.1-mini.")
    args = parser.parse_args()

    verfuegung_path = Path(args.verfuegung)
    beschwerde_path = Path(args.beschwerde) if args.beschwerde else None
    model_name = resolve_model_name(args.model)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = build_output_path(args.output, verfuegung_path, DEFAULT_OUTPUT_DIR, timestamp)
    saved_path = run_with_paths(
        verfuegung_path=verfuegung_path,
        beschwerde_path=beschwerde_path,
        output_path=output_path,
        model_name=model_name,
    )
    print(f"Saved Sachverhalt draft to: {saved_path}")


if __name__ == "__main__":
    main()
