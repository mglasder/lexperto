#!/usr/bin/env python3
"""Run a local smoke check without external API calls."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.models.extraction import Paragraph
from src.structuring import create_paragraph_struct


def main() -> None:
    paragraphs = [
        Paragraph(number="1.", text="Top level"),
        Paragraph(number="1.1", text="Nested child"),
    ]
    structured = create_paragraph_struct(paragraphs)

    assert len(structured) == 1
    assert structured[0].number == "1."
    assert len(structured[0].subparagraphs) == 1
    assert structured[0].subparagraphs[0].number == "1.1"

    print("Smoke check passed.")


if __name__ == "__main__":
    main()
