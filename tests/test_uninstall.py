"""Behavioral tests for the local-only MOSS uninstall helper.

Every test runs inside a throwaway fixture directory (never the real repo tree).
The helper module is loaded directly from its file so these tests do not require
the full SDK (or its optional integrations) to be installed.
"""

import importlib.util
import re
import sys
from pathlib import Path

_UNINSTALL_PATH = Path(__file__).resolve().parent.parent / "moss_openai" / "uninstall.py"
_spec = importlib.util.spec_from_file_location("moss_openai_uninstall", _UNINSTALL_PATH)
uninstall = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(uninstall)

try:
    import tomllib
except ModuleNotFoundError:  # Python < 3.11
    tomllib = None


PYPROJECT = """\
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "demo"
version = "0.0.1"
dependencies = [
    "moss-sdk>=0.3.0",
    "openai>=1.0.0",
    "httpx>=0.27.0",
]
"""

ENV_CONTENT = """\
# leading comment
MOSS_API_KEY=secret123
MOSS_TRUST_URL=https://trust.example
NOT_MOSS_KEY=x
OTHER=MOSS_value

DATABASE_URL=postgres://localhost/db
"""


def _populate_fixture(root: Path) -> None:
    (root / ".moss.yml").write_text("token: abc\n")
    (root / "moss_config.json").write_text('{"key": "v"}\n')
    (root / "moss.config.js").write_text("module.exports = {};\n")
    (root / ".env").write_text(ENV_CONTENT)
    (root / "pyproject.toml").write_text(PYPROJECT)
    # unrelated files that must survive untouched
    (root / "config.json").write_text('{"unrelated": true}\n')
    (root / "settings.yml").write_text("unrelated: yes\n")
    (root / "app.config.js").write_text("export default {};\n")
    (root / ".env.example").write_text("MOSS_API_KEY=changeme\n")
    (root / "main.py").write_text("print('hello')\n")
    # subdir .env must NOT be touched (no recursion)
    sub = root / "subdir"
    sub.mkdir()
    (sub / ".env").write_text("MOSS_API_KEY=subsecret\nKEEP=1\n")


def _run(monkeypatch, args):
    monkeypatch.setattr(sys, "argv", ["moss_openai.uninstall", *args])
    return uninstall.main()


def _snapshot(root: Path) -> dict:
    return {
        p.relative_to(root).as_posix(): p.read_bytes()
        for p in root.rglob("*")
        if p.is_file()
    }


def test_dry_run_exits_zero_and_no_changes(tmp_path, monkeypatch):
    """--dry-run exits 0 and mutates nothing."""
    _populate_fixture(tmp_path)
    monkeypatch.chdir(tmp_path)
    before = _snapshot(tmp_path)

    rc = _run(monkeypatch, ["--dry-run"])

    assert rc == 0
    assert _snapshot(tmp_path) == before


def test_removes_only_moss_config_files(tmp_path, monkeypatch):
    """Real run removes MOSS config files; unrelated files byte-identical."""
    _populate_fixture(tmp_path)
    monkeypatch.chdir(tmp_path)
    before = _snapshot(tmp_path)

    rc = _run(monkeypatch, [])

    assert rc == 0
    assert not (tmp_path / ".moss.yml").exists()
    assert not (tmp_path / "moss_config.json").exists()
    assert not (tmp_path / "moss.config.js").exists()
    for name in ("config.json", "settings.yml", "app.config.js", ".env.example", "main.py"):
        assert (tmp_path / name).read_bytes() == before[name]


def test_env_prefix_key_matching(tmp_path, monkeypatch):
    """Only keys beginning with MOSS_ removed; others preserved."""
    _populate_fixture(tmp_path)
    monkeypatch.chdir(tmp_path)

    _run(monkeypatch, [])

    env = (tmp_path / ".env").read_text()
    assert "MOSS_API_KEY" not in env
    assert "MOSS_TRUST_URL" not in env
    assert "NOT_MOSS_KEY=x" in env
    assert "OTHER=MOSS_value" in env
    assert "# leading comment" in env
    assert "DATABASE_URL=postgres://localhost/db" in env
    assert "\n\n" in env  # blank line preserved


def test_no_subdir_recursion(tmp_path, monkeypatch):
    """.env files in subdirectories are not modified."""
    _populate_fixture(tmp_path)
    monkeypatch.chdir(tmp_path)
    sub_before = (tmp_path / "subdir" / ".env").read_text()

    _run(monkeypatch, [])

    assert (tmp_path / "subdir" / ".env").read_text() == sub_before
    assert "MOSS_API_KEY=subsecret" in (tmp_path / "subdir" / ".env").read_text()


def test_manifest_stays_valid_only_moss_removed(tmp_path, monkeypatch):
    """moss-sdk dep removed, manifest still valid, other deps intact."""
    _populate_fixture(tmp_path)
    monkeypatch.chdir(tmp_path)

    _run(monkeypatch, [])

    text = (tmp_path / "pyproject.toml").read_text()
    assert "moss-sdk" not in text
    assert "openai" in text
    assert "httpx" in text
    if tomllib is not None:
        data = tomllib.loads(text)
        deps = data["project"]["dependencies"]
        assert not any("moss-sdk" in d for d in deps)
        assert any("openai" in d for d in deps)
        assert any("httpx" in d for d in deps)


def test_requirements_txt_dependency_removed(tmp_path, monkeypatch):
    """moss-sdk stripped from requirements.txt, other requirements kept."""
    (tmp_path / "requirements.txt").write_text(
        "moss-sdk>=0.3.0\nopenai>=1.0.0\nhttpx>=0.27.0\n"
    )
    monkeypatch.chdir(tmp_path)

    _run(monkeypatch, [])

    reqs = (tmp_path / "requirements.txt").read_text()
    assert "moss-sdk" not in reqs
    assert "openai>=1.0.0" in reqs
    assert "httpx>=0.27.0" in reqs


def test_idempotent_empty_dir(tmp_path, monkeypatch):
    """Nothing to clean -> no crash, exit 0, no files created/deleted."""
    monkeypatch.chdir(tmp_path)

    rc = _run(monkeypatch, [])

    assert rc == 0
    assert list(tmp_path.iterdir()) == []


def test_idempotent_second_run(tmp_path, monkeypatch):
    """A second real run after a full clean is a benign no-op that still exits 0."""
    _populate_fixture(tmp_path)
    monkeypatch.chdir(tmp_path)
    assert _run(monkeypatch, []) == 0
    after_first = _snapshot(tmp_path)

    assert _run(monkeypatch, []) == 0
    assert _snapshot(tmp_path) == after_first


def test_dry_run_real_parity(tmp_path, monkeypatch):
    """The plan claimed by --dry-run equals what the real run acts on."""
    _populate_fixture(tmp_path)
    monkeypatch.chdir(tmp_path)

    dry_configs = uninstall.remove_config_files(dry_run=True)
    dry_env = uninstall.remove_env_vars(dry_run=True)
    dry_dep = uninstall.remove_dependency(dry_run=True)
    # dry-run mutated nothing
    assert (tmp_path / ".moss.yml").exists()
    assert "MOSS_API_KEY" in (tmp_path / ".env").read_text()

    real_configs = uninstall.remove_config_files(dry_run=False)
    real_env = uninstall.remove_env_vars(dry_run=False)
    real_dep = uninstall.remove_dependency(dry_run=False)

    assert dry_configs == real_configs
    assert dry_env == real_env
    assert dry_dep == real_dep


def test_prints_manual_checklist(tmp_path, monkeypatch, capsys):
    """Checklist enumerates the real un-automatable steps."""
    monkeypatch.chdir(tmp_path)

    _run(monkeypatch, ["--dry-run"])

    out = capsys.readouterr().out
    assert "MANUAL CLEANUP CHECKLIST" in out
    assert "Revoke/rotate MOSS credentials" in out
    assert "MOSS_* secrets from GitHub Actions" in out
    assert "Dockerfiles" in out
    assert "Docs" in out


def test_no_network_imports():
    """The helper performs no network/API calls (local-only)."""
    source = _UNINSTALL_PATH.read_text()
    for token in ("requests", "urllib", "socket", "httpx", "http.client", "aiohttp"):
        assert not re.search(rf"\b(import|from)\b.*\b{re.escape(token)}\b", source), token
