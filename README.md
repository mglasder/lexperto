# Lexperto

A legal document analysis and extraction system.

## Project Structure

```
lexperto/
├── src/                      # Main project code
│   ├── __init__.py
│   ├── annotation.py         # Annotation logic
│   ├── extraction.py         # Extraction logic
│   ├── structuring.py        # Structuring logic
│   ├── utils.py              # Utility functions
│   └── models/               # ML models and related code
│       ├── __init__.py
│       ├── extraction.py
│       ├── items.py
│       ├── prompt.py
│       ├── results.py
│       └── state.py
│
├── experiments/              # Experimental code and scripts
│   ├── __init__.py
│   ├── experiment.py
│   ├── hierarchy.py
│   ├── lexperto.py
│   ├── multiagents.py
│   ├── preprocessing.py
│   ├── scraping.py
│   ├── search.py
│   └── trylang.py
│
├── prompts/                  # All prompt-related content
│   ├── aerw/
│   ├── annotation/
│   ├── experimental/
│   ├── instructions/
│   ├── kerw/
│   ├── multi/
│   ├── sach/
│   ├── test/
│   └── prompts.py
│
├── data/                     # Data directories
│   ├── input/
│   ├── output/
│   ├── urteile/
│   └── urteile_html/
│
├── tests/                    # Test files
├── run_logs/                 # Log files
├── scripts/                  # Helper scripts
├── pyproject.toml            # Black config
├── README.md                 # Project documentation
├── implementation-plan.md    # Implementation plan
├── master-schema-phase-1.md  # Master schema phase 1
├── master-schema.md          # Master schema
└── environment.yml           # Conda environment file
```

## Setup (Recommended: Conda + pip)

1. Create a new conda environment with only Python (no dependencies):

```bash
conda create -n jurabot311 python=3.11
conda activate jurabot311
```

2. Install all project dependencies using pip:

```bash
pip install -r requirements.txt
```

## Development

- Core functionality is in the `src/` directory
- Experimental code is in the `experiments/` directory
- All prompts are managed in the `prompts/` directory
- Tests are in the `tests/` directory

## Simple Git Operations (Windows)

Open the Anaconda Prompt or Command Prompt and navigate to your project directory:

### Pull latest changes
```
git pull
```

### Add changes
```
git add <file_or_folder>
git add . //adds all changed files
```

### Commit changes locally
```
git commit -m "Your commit message"
```

### Push changes to remote repo
```
git push
```

### Create a new branch
```
git checkout -b new-branch-name
```

### Switch to an existing branch
```
git checkout branch-name
```

## Documentation

- `implementation-plan.md`: Overall implementation plan
- `master-schema.md`: Master schema documentation
- `master-schema-phase-1.md`: Master schema phase 1



