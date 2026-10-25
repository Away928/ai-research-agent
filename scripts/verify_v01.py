"""Reproducible, no-key acceptance checks for the local v0.1 MVP.

Run from the installed app environment:
    python scripts/verify_v01.py

This runner never invokes real financial APIs or LLMs; tests use synthetic data
or mocks and the HTML is generated in a temporary directory.
It does not imply that the Git repository is approved for public release.
"""

from pathlib import Path
from importlib.util import find_spec
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]


def check(name: str, args) -> None:
    print("\n== {} ==".format(name), flush=True)
    subprocess.run(
        [sys.executable] + list(args),
        cwd=str(ROOT),
        check=True,
    )


def main() -> int:
    missing = [module for module in ("pytest", "streamlit", "pandas")
               if find_spec(module) is None]
    if missing:
        print(
            "Missing application/test dependencies: " + ", ".join(missing)
            + ". Install requirements.txt into the current Python environment first.",
            file=sys.stderr,
        )
        return 2
    check("Local unit and regression tests", [
        "-m", "pytest", "-q", "-p", "no:cacheprovider",
    ])
    check("Demo Streamlit interaction", [
        "scripts/verify_demo.py",
    ])
    check("Real research Streamlit interaction with fake backend", [
        "scripts/verify_real_entry.py",
    ])
    check("CLI startup without running research", [
        "cli.py", "--help",
    ])
    with tempfile.TemporaryDirectory(prefix="research-agent-v01-") as directory:
        output = Path(directory) / "synthetic-demo.html"
        check("Standalone HTML export without network or LLM", [
            "scripts/export_demo.py", "--output", str(output),
        ])
        assert output.exists()
        document = output.read_text(encoding="utf-8")
        assert output.stat().st_size > 10_000
        assert "<html lang=\"zh-CN\">" in document
        assert "纯合成" in document
        assert "未调用大模型" in document
        assert "FIN-TST001-roe_pct" in document
        assert "<script" not in document.lower()
    print(
        "\nPASS: v0.1 local acceptance checks completed.\n"
        "NOT VERIFIED: paid LLM execution, live supplier data, original-filing "
        "agreement, privacy clearance or public-release safety.",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
