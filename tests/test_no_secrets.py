"""No API key or secret in the repository (OB4 §3 "make sure that your project does not include Claude API key")."""
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
API_KEY = re.compile(r"sk-ant-[A-Za-z0-9_-]{10,}")
# A filled-in value in an env-style file (.env.example must keep the values empty)
ENV_VALUE = re.compile(r"^[ \t]*(ANTHROPIC_API_KEY|SECRET_KEY)[ \t]*=[ \t]*[^\s#]", re.M)


def tracked_files():
    result = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, check=True)
    return [ROOT / name for name in result.stdout.splitlines()]


def test_no_api_key_in_tracked_files():
    found = []
    for path in tracked_files():
        if not path.is_file() or path.suffix in {".png", ".jpg", ".pdf", ".docx"}:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        if API_KEY.search(text) or (path.name.startswith(".env") and ENV_VALUE.search(text)):
            found.append(str(path.relative_to(ROOT)))
    assert found == []


def test_env_file_is_ignored():
    result = subprocess.run(["git", "check-ignore", ".env"], cwd=ROOT, capture_output=True, text=True)
    assert result.returncode == 0, ".env must be git-ignored"
