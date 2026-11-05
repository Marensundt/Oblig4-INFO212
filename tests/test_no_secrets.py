"""No API key or secret in the repository (OB4 §3 "make sure that your project does not include Claude API key").

`test_smoke.test_no_api_keys_in_source` scans all source files for Claude keys; this file adds the
git-specific checks: no filled-in values in tracked env files, and `.env` itself is ignored.
"""
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# A filled-in value in an env-style file (.env.example must keep the values empty)
ENV_VALUE = re.compile(r"^[ \t]*(ANTHROPIC_API_KEY|SECRET_KEY|NEO4J_PASSWORD)[ \t]*=[ \t]*[^\s#]", re.M)


def tracked_files():
    result = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, check=True)
    return [ROOT / name for name in result.stdout.splitlines()]


def test_no_secret_values_in_tracked_env_files():
    env_files = [path for path in tracked_files() if path.name.startswith(".env") and path.is_file()]
    assert env_files, ".env.example should be tracked"
    found = [str(path.relative_to(ROOT)) for path in env_files
             if ENV_VALUE.search(path.read_text(encoding="utf-8"))]
    assert found == []


def test_env_file_is_ignored():
    result = subprocess.run(["git", "check-ignore", ".env"], cwd=ROOT, capture_output=True, text=True)
    assert result.returncode == 0, ".env must be git-ignored"
