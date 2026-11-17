"""Check that the pinned Open Food Facts revision is still resolvable upstream.

The repository's reproducibility claim rests on one pinned commit and its
SHA-256 (see `data/reference/pinned_sources.json`). This script asks the
Hugging Face API whether that revision still exists and how far the public
dataset has moved since, so the claim can be checked without downloading the
multi-gigabyte Parquet file.

The check is read-only and needs the network, so it is deliberately not wired
into CI, which must stay offline. Drift describes the moment it is measured,
which is why the script prints it instead of the repository recording it as a
fixed number.
"""

import argparse
import json
import urllib.error
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date

from support_pinned_inputs import SNAPSHOT_COMMIT, SNAPSHOT_REPOSITORY

API_BASE = "https://huggingface.co/api/datasets"
USER_AGENT = "indonesia-food-product-landscape/1.0"
DEFAULT_TIMEOUT_SECONDS = 30.0


@dataclass(frozen=True)
class PinStatus:
    repository: str
    pinned_commit: str
    pinned_date: date | None
    resolvable: bool
    head_commit: str | None
    head_date: date | None


def fetch_json(url: str, timeout: float = DEFAULT_TIMEOUT_SECONDS) -> dict:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        payload = json.load(response)
    if not isinstance(payload, dict):
        raise ValueError(f"Expected a JSON object from {url}.")
    return payload


def parse_iso_date(value: object) -> date | None:
    if not isinstance(value, str):
        return None
    try:
        return date.fromisoformat(value[:10])
    except ValueError:
        return None


def pin_status(
    repository: str,
    commit: str,
    fetch: Callable[[str], dict] = fetch_json,
) -> PinStatus:
    try:
        revision = fetch(f"{API_BASE}/{repository}/revision/{commit}")
    except urllib.error.HTTPError as error:
        if error.code == 404:
            return PinStatus(repository, commit, None, False, None, None)
        raise

    resolvable = str(revision.get("sha", "")).lower() == commit.lower()

    head_commit: str | None = None
    try:
        head = fetch(f"{API_BASE}/{repository}")
    except urllib.error.HTTPError:
        head = {}
    reported_head = head.get("sha")
    if isinstance(reported_head, str):
        head_commit = reported_head

    return PinStatus(
        repository=repository,
        pinned_commit=commit,
        pinned_date=parse_iso_date(revision.get("lastModified")),
        resolvable=resolvable,
        head_commit=head_commit,
        head_date=parse_iso_date(head.get("lastModified")),
    )


def drift_days(status: PinStatus) -> int | None:
    if status.pinned_date is None or status.head_date is None:
        return None
    return (status.head_date - status.pinned_date).days


def format_report(status: PinStatus) -> str:
    drift = drift_days(status)
    if drift is None:
        drift_text = "unknown"
    elif drift > 0:
        drift_text = f"{drift} days since the pinned commit"
    elif drift == 0:
        drift_text = "none (same day)"
    else:
        drift_text = f"{abs(drift)} days ahead of the current head"

    lines = [
        f"Repository     : {status.repository}",
        f"Pinned commit  : {status.pinned_commit} ({_format_date(status.pinned_date)})",
        f"Pin resolvable : {'yes' if status.resolvable else 'no'}",
        f"Current head   : {_format_commit(status.head_commit)} "
        f"({_format_date(status.head_date)})",
        f"Drift          : {drift_text}",
        "",
    ]
    if status.resolvable:
        lines.append(
            "Drift measures how far the public dataset has moved, not whether this "
            "study's numbers are wrong: the pinned commit and SHA-256 define "
            "reproducibility."
        )
    else:
        lines.append(
            "This revision is no longer resolvable upstream, so the snapshot cannot "
            "be rebuilt from the recorded pin. Re-establish the pin before any claim "
            "that depends on re-downloading the source."
        )
    return "\n".join(lines)


def _format_date(value: date | None) -> str:
    return value.isoformat() if value is not None else "unknown"


def _format_commit(value: str | None) -> str:
    return value if value is not None else "unknown"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", default=SNAPSHOT_REPOSITORY)
    parser.add_argument("--commit", default=SNAPSHOT_COMMIT)
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT_SECONDS)
    args = parser.parse_args()

    try:
        status = pin_status(
            args.repository,
            args.commit,
            lambda url: fetch_json(url, args.timeout),
        )
    except (urllib.error.URLError, TimeoutError, ValueError) as error:
        print(f"Could not read pin status from {API_BASE}: {error}")
        print("This check needs network access and is not part of the offline suite.")
        return 2

    print(format_report(status))
    return 0 if status.resolvable else 1


if __name__ == "__main__":
    raise SystemExit(main())
