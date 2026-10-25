"""Read-only release-path preflight, including paths in reachable Git history.

This is a *path* triage guard, not an exhaustive security or licensing scan.
A clean result does not make the repository safe to publish.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path


def path_risk(path: str) -> tuple[str, str] | None:
    """Classify known sensitive/review-required paths without reading contents."""
    path = path.strip().replace("\\", "/")
    if not path:
        return None
    name = Path(path).name
    if path.startswith("user_data/") or path.startswith("private/"):
        return ("block", "personal_or_user_material")
    if name == ".env" or name.startswith(".env.") or name in (
        "secrets.toml", "credentials.json", "service_account.json",
    ) or name.endswith((".pem", ".key", ".p12", ".pfx")):
        return ("block", "secrets_or_private_key_path")
    if path.startswith(".claude/"):
        return ("review", "machine_specific_configuration")
    if path.startswith("demo_output/") and name not in ("README.md", ".gitkeep"):
        return ("review", "generated_research_reports")
    return None


def classify_paths(tracked: list[str], history: list[str]) -> dict:
    """Detect tracked risks and historical remnants; do not erase history."""
    result = {
        "tracked_blockers": {},
        "history_blockers": {},
        "tracked_review": {},
        "history_review": {},
    }
    for key, paths in (("tracked", tracked), ("history", history)):
        seen = set()
        for path in paths:
            if path in seen:
                continue
            seen.add(path)
            risk = path_risk(path)
            if risk is None:
                continue
            severity, reason = risk
            bucket = result[f"{key}_{'blockers' if severity == 'block' else 'review'}"]
            bucket[reason] = bucket.get(reason, 0) + 1
    return result


def _git_paths(repo: Path, *args: str) -> list[str]:
    completed = subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True, check=True,
    )
    return [entry.decode("utf-8", errors="replace").strip()
            for entry in completed.stdout.split(b"\0") if entry.strip()]


def main() -> int:
    repo = Path(__file__).resolve().parents[1]
    try:
        tracked = _git_paths(repo, "ls-files", "-z")
        history = _git_paths(repo, "log", "--all", "--format=", "--name-only", "-z")
    except (OSError, subprocess.CalledProcessError) as exc:
        print(json.dumps({"error": type(exc).__name__,
                          "release_ready": False}, ensure_ascii=False))
        return 2
    summary = classify_paths(tracked, history)
    print(json.dumps({
        "release_ready": False,
        "reason": ("blocking or review-required paths found"
                   if any(summary.values())
                   else "path checks alone cannot certify release safety"),
        "checks": summary,
        "limitations": "Does not read file contents, detect secrets by value, or certify licenses.",
    }, ensure_ascii=False, indent=2))
    # Treat review-required paths as an unresolved release gate too.
    # Exit zero only when the path triage finds no known issues, not as a safety certificate.
    return 2 if any(summary.values()) else 0


if __name__ == "__main__":
    raise SystemExit(main())
