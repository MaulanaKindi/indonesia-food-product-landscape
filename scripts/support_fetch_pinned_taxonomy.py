"""Fetch the locally excluded category taxonomy snapshot when it is missing."""

import hashlib
import json
import os
import tempfile
import urllib.error
import urllib.request
from pathlib import Path

from support_pinned_inputs import (
    TAXONOMY_FILE,
    TAXONOMY_SHA256,
    TAXONOMY_SIZE_BYTES,
    TAXONOMY_URL,
)

TARGET_FILE = TAXONOMY_FILE
SOURCE_URL = TAXONOMY_URL
EXPECTED_SIZE_BYTES = TAXONOMY_SIZE_BYTES
EXPECTED_SHA256 = TAXONOMY_SHA256
CHUNK_SIZE_BYTES = 1024 * 1024


def validate_snapshot_metadata(size: int, sha256: str) -> None:
    if size != EXPECTED_SIZE_BYTES or sha256.upper() != EXPECTED_SHA256:
        raise ValueError(
            "Category taxonomy does not match the pinned snapshot: "
            f"expected {EXPECTED_SIZE_BYTES} bytes and SHA-256 "
            f"{EXPECTED_SHA256}; found {size} bytes and {sha256.upper()}. "
            "The upstream taxonomy URL is mutable; obtain the exact archived "
            "snapshot before rerunning the analysis."
        )


def hash_file(path: Path) -> tuple[int, str]:
    digest = hashlib.sha256()
    size = 0
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(CHUNK_SIZE_BYTES), b""):
            size += len(chunk)
            digest.update(chunk)
    return size, digest.hexdigest().upper()


def validate_json_syntax(raw_bytes: bytes) -> dict:
    try:
        taxonomy = json.loads(raw_bytes)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Category taxonomy is not valid JSON: {exc}") from exc
    return taxonomy


def validate_taxonomy_structure(taxonomy: dict) -> None:
    if not isinstance(taxonomy, dict):
        raise ValueError(
            "Category taxonomy must be a JSON object mapping tags to entries; "
            f"found {type(taxonomy).__name__}."
        )
    for tag, entry in taxonomy.items():
        if not isinstance(tag, str):
            raise ValueError(
                f"Category taxonomy keys must be strings; found "
                f"{type(tag).__name__} for key {tag!r}."
            )
        if not isinstance(entry, dict):
            raise ValueError(
                f"Category taxonomy entry for {tag!r} must be an object; "
                f"found {type(entry).__name__}."
            )
        parents = entry.get("parents", [])
        if not isinstance(parents, list):
            raise ValueError(
                f"Category taxonomy entry for {tag!r} has invalid 'parents': "
                f"expected a list, found {type(parents).__name__}."
            )
        for parent in parents:
            if not isinstance(parent, str):
                raise ValueError(
                    f"Category taxonomy entry for {tag!r} has a non-string "
                    f"parent; found {type(parent).__name__}."
                )
        name = entry.get("name", {})
        if not isinstance(name, dict):
            raise ValueError(
                f"Category taxonomy entry for {tag!r} has invalid 'name': "
                f"expected an object, found {type(name).__name__}."
            )


def load_validated_taxonomy(path: Path) -> dict:
    raw_bytes = path.read_bytes()
    size, sha256 = hash_file(path)
    validate_snapshot_metadata(size, sha256)
    taxonomy = validate_json_syntax(raw_bytes)
    validate_taxonomy_structure(taxonomy)
    return taxonomy


def verify_file(path: Path) -> None:
    load_validated_taxonomy(path)


def download_if_missing() -> None:
    TARGET_FILE.parent.mkdir(parents=True, exist_ok=True)
    if TARGET_FILE.exists():
        verify_file(TARGET_FILE)
        print(f"Verified existing taxonomy snapshot: {TARGET_FILE}")
        return

    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            prefix=".categories.json.",
            suffix=".download",
            dir=TARGET_FILE.parent,
            delete=False,
        ) as temporary_file:
            temporary_path = Path(temporary_file.name)
            digest = hashlib.sha256()
            size = 0
            request = urllib.request.Request(
                SOURCE_URL,
                headers={"User-Agent": "indonesia-food-product-landscape/1.0"},
            )
            try:
                with urllib.request.urlopen(request, timeout=60) as response:
                    while chunk := response.read(CHUNK_SIZE_BYTES):
                        try:
                            temporary_file.write(chunk)
                        except OSError as exc:
                            raise ValueError(
                                f"Could not write the taxonomy download to "
                                f"{temporary_path}: {exc}."
                            ) from exc
                        digest.update(chunk)
                        size += len(chunk)
            except urllib.error.URLError as exc:
                raise ValueError(
                    f"Could not download the category taxonomy from "
                    f"{SOURCE_URL}: {exc.reason}. "
                    "The upstream taxonomy URL is mutable; obtain the exact "
                    "archived snapshot before rerunning the analysis."
                ) from exc
            except TimeoutError as exc:
                raise ValueError(
                    f"Download of the category taxonomy from {SOURCE_URL} "
                    "timed out. Obtain the exact archived snapshot before "
                    "rerunning the analysis."
                ) from exc
            except OSError as exc:
                raise ValueError(
                    f"Could not download the category taxonomy from "
                    f"{SOURCE_URL}: {exc}. "
                    "Obtain the exact archived snapshot before rerunning "
                    "the analysis."
                ) from exc
            try:
                temporary_file.flush()
                os.fsync(temporary_file.fileno())
            except OSError as exc:
                raise ValueError(
                    f"Could not write the taxonomy download to {temporary_path}: {exc}."
                ) from exc

        validate_snapshot_metadata(size, digest.hexdigest())
        load_validated_taxonomy(temporary_path)
        temporary_path.replace(TARGET_FILE)
        print(f"Downloaded and verified taxonomy snapshot: {TARGET_FILE}")
    finally:
        if temporary_path is not None and temporary_path.exists():
            temporary_path.unlink()


if __name__ == "__main__":
    download_if_missing()
