from pathlib import Path
import re

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_script_filenames_distinguish_stages_from_support_tools() -> None:
    scripts = PROJECT_ROOT / "scripts"
    names = {path.name for path in scripts.glob("*.py")}
    assert "run_all.py" in names
    for name in names - {"run_all.py"}:
        assert re.fullmatch(r"(?:\d{2}_[a-z0-9_]+|support_[a-z0-9_]+)\.py", name)


def test_project_documentation_filenames_use_ordered_snake_case() -> None:
    documentation = PROJECT_ROOT / "docs"
    for path in documentation.glob("*.md"):
        assert re.fullmatch(r"\d{2}_[a-z0-9_]+\.md", path.name)
