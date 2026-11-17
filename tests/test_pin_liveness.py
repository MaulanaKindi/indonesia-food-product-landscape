import importlib.util
import json
import sys
import urllib.error
from datetime import date
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = str(PROJECT_ROOT / "scripts")
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

PIN_SPEC = importlib.util.spec_from_file_location(
    "support_check_pin_liveness",
    PROJECT_ROOT / "scripts" / "support_check_pin_liveness.py",
)
pin = importlib.util.module_from_spec(PIN_SPEC)
PIN_SPEC.loader.exec_module(pin)

API_BASE = pin.API_BASE
REPOSITORY = pin.SNAPSHOT_REPOSITORY
PINNED_COMMIT = pin.SNAPSHOT_COMMIT
REVISION_URL = f"{API_BASE}/{REPOSITORY}/revision/{PINNED_COMMIT}"
REPOSITORY_URL = f"{API_BASE}/{REPOSITORY}"

PINNED_REVISION = {"sha": PINNED_COMMIT, "lastModified": "2026-10-23T08:01:20.000Z"}
CURRENT_HEAD = {
    "sha": "f2c887f344701a3d6ad7b0d3fa9626a842088789",
    "lastModified": "2026-11-16T11:03:24.000Z",
}


def fetch_from(responses):
    def fetch(url):
        if url not in responses:
            raise AssertionError(f"unexpected request for {url}")
        payload = responses[url]
        if isinstance(payload, Exception):
            raise payload
        return payload

    return fetch


def test_resolvable_pin_reports_drift_from_the_current_head():
    status = pin.pin_status(
        REPOSITORY,
        PINNED_COMMIT,
        fetch_from({REVISION_URL: PINNED_REVISION, REPOSITORY_URL: CURRENT_HEAD}),
    )
    assert status.resolvable is True
    assert status.pinned_date == date(2026, 10, 23)
    assert status.head_commit == CURRENT_HEAD["sha"]
    assert pin.drift_days(status) == 24


def test_sha_mismatch_is_not_resolvable():
    status = pin.pin_status(
        REPOSITORY,
        PINNED_COMMIT,
        fetch_from(
            {
                REVISION_URL: {
                    "sha": "0" * 40,
                    "lastModified": "2026-10-23T08:01:20.000Z",
                },
                REPOSITORY_URL: CURRENT_HEAD,
            }
        ),
    )
    assert status.resolvable is False


def test_missing_revision_is_not_resolvable_and_skips_the_head_request():
    missing = urllib.error.HTTPError(
        REVISION_URL, 404, "Revision not found", None, None
    )
    status = pin.pin_status(
        REPOSITORY, PINNED_COMMIT, fetch_from({REVISION_URL: missing})
    )
    assert status.resolvable is False
    assert status.head_commit is None
    assert pin.drift_days(status) is None


def test_unknown_head_leaves_drift_unknown():
    server_error = urllib.error.HTTPError(
        REPOSITORY_URL, 500, "Server error", None, None
    )
    status = pin.pin_status(
        REPOSITORY,
        PINNED_COMMIT,
        fetch_from({REVISION_URL: PINNED_REVISION, REPOSITORY_URL: server_error}),
    )
    assert status.resolvable is True
    assert status.head_commit is None
    assert pin.drift_days(status) is None


def test_report_states_drift_and_the_limit_of_the_measure():
    status = pin.pin_status(
        REPOSITORY,
        PINNED_COMMIT,
        fetch_from({REVISION_URL: PINNED_REVISION, REPOSITORY_URL: CURRENT_HEAD}),
    )
    report = pin.format_report(status)
    assert "24 days since the pinned commit" in report
    assert "Pin resolvable : yes" in report
    assert "pinned commit and SHA-256 define" in report


def test_report_warns_when_the_pin_is_gone():
    missing = urllib.error.HTTPError(
        REVISION_URL, 404, "Revision not found", None, None
    )
    status = pin.pin_status(
        REPOSITORY, PINNED_COMMIT, fetch_from({REVISION_URL: missing})
    )
    report = pin.format_report(status)
    assert "Pin resolvable : no" in report
    assert "no longer resolvable upstream" in report


def test_parse_iso_date_accepts_timestamps_and_rejects_garbage():
    assert pin.parse_iso_date("2026-11-16T11:03:24.000Z") == date(2026, 11, 16)
    assert pin.parse_iso_date(None) is None
    assert pin.parse_iso_date("not-a-date") is None


def test_defaults_come_from_the_pinned_manifest():
    manifest = json.loads(
        (PROJECT_ROOT / "data" / "reference" / "pinned_sources.json").read_text(
            encoding="utf-8"
        )
    )
    snapshot = manifest["open_food_facts_snapshot"]
    assert pin.SNAPSHOT_COMMIT == snapshot["commit"]
    assert pin.SNAPSHOT_REPOSITORY == snapshot["repository"]
