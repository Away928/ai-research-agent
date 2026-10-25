"""Pure tests for historical privacy path classification."""

from tools.release_safety import classify_paths, path_risk


def test_private_upload_and_secret_paths_block():
    assert path_risk("user_data/interview.md")[0] == "block"
    assert path_risk(".streamlit/secrets.toml")[0] == "block"
    assert path_risk(".env.production")[0] == "block"
    assert path_risk("certs/private.key")[0] == "block"


def test_demo_and_local_config_require_review():
    assert path_risk("demo_output/report.md")[0] == "review"
    assert path_risk(".claude/settings.local.json")[0] == "review"
    assert path_risk("demo_output/README.md") is None


def test_history_flagged_even_after_current_deletion():
    report = classify_paths(
        ["README.md", "tools/claim_audit.py"],
        ["user_data/private.md", "demo_output/report.md", "user_data/private.md"],
    )
    assert report["tracked_blockers"] == {}
    assert report["history_blockers"] == {"personal_or_user_material": 1}
    assert report["history_review"] == {"generated_research_reports": 1}


def test_no_files_not_equivalent_to_safety_certificate():
    result = classify_paths([], [])
    assert all(not section for section in result.values())
