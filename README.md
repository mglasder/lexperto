# Lexperto

A legal document analysis and extraction system.

## Project Structure

```
lexperto/
├── src/                      # Main project code
│   ├── core/                 # Core functionality
│   │   ├── extraction.py     # Main extraction logic
│   │   ├── preprocessing.py  # Data preprocessing
│   │   ├── search.py        # Search functionality
│   │   └── store.py         # Data storage
│   ├── models/              # ML models and related code
│   └── utils/               # Utility functions
│       └── helpers.py       # Helper functions
│
├── experiments/             # Experimental code and scripts
│   ├── multiagents.py      # Multi-agent experiments
│   ├── hierarchy.py        # Hierarchy experiments
│   ├── trylang.py         # Language experiments
│   └── experiment.py       # General experiments
│
├── prompts/                # All prompt-related content
│   ├── production/        # Production prompts
│   ├── test/             # Test prompts
│   └── experimental/      # Experimental prompts
│
├── data/                   # Data directories
│   ├── input/             # Input data
│   ├── output/            # Output data
│   ├── urteile/           # Court decisions
│   └── urteile_html/      # HTML versions of court decisions
│
├── tests/                 # Test files
└── run_logs/             # Log files
```

## Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
Create a `.env` file in the root directory with:
```
OPENAI_API_KEY=your_api_key_here
```

## Usage

### Main Extraction

The core extraction functionality is in `src/core/extraction.py`. To run the extraction:

```bash
python -m src.core.extraction <pdf_name>
```

### Experiments

Experimental code is located in the `experiments/` directory. Each experiment can be run independently:

```bash
python -m experiments.multiagents
python -m experiments.hierarchy
python -m experiments.trylang
```

## Development

- Core functionality is in the `src/` directory
- Experimental code is in the `experiments/` directory
- All prompts are managed in the `prompts/` directory
- Tests are in the `tests/` directory

## Documentation

- `implementation-plan.md`: Overall implementation plan
- `lang_01.md`: Language model documentation
- `Struktur.docx`: Detailed structure documentation

## Overview

LexPerto uses large language models to analyze legal documents and generate draft court rulings. This tool aims to assist legal professionals by automating the initial drafting process while maintaining accuracy and adhering to legal standards.

## Release Announcement

### LexPerto 0.1
Lexperto veröffentlicht die Version 0.1 seiner Software, mit der der Sachverhalt und die abstrakten Erwägungen automatisch
auf Basis der Beschwerde und Verfügung generiert werden. Die Software hat noch kein GUI, sondern man kann die notwendige Funktion in Python ausführen.
Das Ergebnis wird als Word-Dokument gespeichert.

### Lexperto 0.2

Lexperto veröffentlicht eine Integration in Microsoft Word, die es ermöglicht, die Generierung von Sachverhalt und abstrakten Erwägungen, direkt in Word zu generieren.
Man kann den entsprechenden Case-Folder spezifizieren und auf Generieren klicken. Danach kann man wie gewohnt im Word Dokument weiterarbeiten.

### Lexperto 0.3

Lexperto veröffentlich eine Version die automatisiert auf Basis von max. 5 Gerichtsurteilen, die Struktur des Dokument automatisch generiert.
Und aus Basis von Input-Dokumenten (Beschwerde, Verfügung) den Sachverhalt und die abstrakten Erwägungen generiert. Zuerst wird eine generisches Dokument generiert, welches der Nutzer
anpassen kann. Dieses wird dann in Word geöffnet, der Case-Folder ausgewählt und die spezifische Generierung gestartet.

## Features

- Process legal documents in various formats (PDF, DOCX, TXT)
- Generate structured court ruling drafts
- Customize output based on jurisdiction and case type
- Maintain references to source materials

