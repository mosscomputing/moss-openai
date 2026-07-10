"""MOSS Uninstall Helper for moss-openai.

Usage:
    python -m moss_openai.uninstall [--dry-run]

Local-only cleanup. Does NOT call any API.
"""

import argparse
import re
import sys
from pathlib import Path

CONFIG_FILES = [".moss.yml", "moss_config.json", "moss.config.js"]
ENV_FILES = [".env", ".env.local", ".env.development", ".env.production"]
DIST_NAME = "moss-openai"  # display name
DEP_PATTERN = r"moss[-_]sdk"  # dependency actually declared by this repo


def remove_config_files(dry_run: bool) -> list[str]:
    removed = []
    for name in CONFIG_FILES:
        path = Path(name)
        if path.exists():
            print(f"[DRY-RUN] Would remove: {path}" if dry_run else f"Removed: {path}")
            if not dry_run:
                path.unlink()
            removed.append(str(path))
    return removed


def remove_env_vars(dry_run: bool) -> list[str]:
    removed = []
    pattern = re.compile(r"^MOSS_[^=\s]*=.*$", re.MULTILINE)
    for name in ENV_FILES:
        path = Path(name)
        if not path.exists():
            continue
        content = path.read_text()
        matches = pattern.findall(content)
        if matches:
            print(
                f"[DRY-RUN] Would remove from {path}: {len(matches)} MOSS_* vars"
                if dry_run
                else f"Removed {len(matches)} MOSS_* vars from {path}"
            )
            if not dry_run:
                new_content = re.sub(r"\n{3,}", "\n\n", pattern.sub("", content))
                path.write_text(new_content)
            removed.extend(matches)
    return removed


def remove_dependency(dry_run: bool) -> bool:
    changed = False
    for manifest in ("requirements.txt", "pyproject.toml"):
        path = Path(manifest)
        if not path.exists():
            continue
        content = path.read_text()
        if manifest == "requirements.txt":
            pat = re.compile(rf"^{DEP_PATTERN}.*$", re.MULTILINE | re.IGNORECASE)
        else:
            pat = re.compile(rf'["\']{DEP_PATTERN}[^"\']*["\'],?\s*\n?', re.IGNORECASE)
        if pat.search(content):
            print(
                f"[DRY-RUN] Would remove {DEP_PATTERN} from {manifest}"
                if dry_run
                else f"Removed {DEP_PATTERN} from {manifest}"
            )
            if not dry_run:
                path.write_text(pat.sub("", content))
            changed = True
    return changed


def print_manual_checklist() -> None:
    print("\n" + "=" * 60)
    print("MANUAL CLEANUP CHECKLIST")
    print("=" * 60)
    print(
        "\n"
        "[ ] Revoke/rotate MOSS credentials in the MOSS console\n"
        "    - Revoke MOSS API keys / capability tokens\n"
        "    - If agents used MOSS capability tokens, revoke those agent credentials\n"
        "[ ] CI/CD: remove MOSS_API_KEY and other MOSS_* secrets from GitHub Actions / CI env\n"
        "[ ] Docker: remove MOSS_* ENV lines and the MOSS dependency from Dockerfiles\n"
        f"[ ] Code: remove imports of {DIST_NAME} from your source\n"
        "[ ] Docs: update README / setup guides that reference MOSS\n"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="MOSS Uninstall Helper")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    print(f"MOSS Uninstall Helper for {DIST_NAME}")
    print("-" * 40)
    if args.dry_run:
        print("[DRY-RUN MODE - No changes will be made]\n")
    remove_config_files(args.dry_run)
    remove_env_vars(args.dry_run)
    remove_dependency(args.dry_run)
    print_manual_checklist()
    print("\n[DRY-RUN] No changes made." if args.dry_run else "\nUninstall complete.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
