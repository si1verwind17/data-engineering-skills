import ast
from pathlib import Path

DAGS = Path(__file__).resolve().parent.parent / "dags"


def test_dags_parse():
    for f in DAGS.glob("*.py"):
        ast.parse(f.read_text())
