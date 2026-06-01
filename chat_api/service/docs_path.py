from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DOCS_DIR = BASE_DIR / "docs"

def doc(*parts):
    return str(DOCS_DIR.joinpath(*parts))
