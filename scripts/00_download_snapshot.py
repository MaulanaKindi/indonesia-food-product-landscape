"""Download the pinned Open Food Facts Parquet snapshot if it is not present."""

import hashlib
import os
import tempfile
import urllib.request
from pathlib import Path

from support_pinned_inputs import (
    SNAPSHOT_COMMIT,
    SNAPSHOT_FILE,
    SNAPSHOT_SHA256,
    SNAPSHOT_SIZE_BYTES,
    SNAPSHOT_URL,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
TARGET_FILE = SNAPSHOT_FILE
EXPECTED_SIZE_BYTES = SNAPSHOT_SIZE_BYTES
EXPECTED_SHA256 = SNAPSHOT_SHA256
CHUNK_SIZE_BYTES = 8 * 1024 * 1024


def hash_file(path: Path) -> tuple[int, str]:
    digest = hashlib.sha256()
    size = 0
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(CHUNK_SIZE_BYTES), b""):
            size += len(chunk)
            digest.update(chunk)
    return size, digest.hexdigest().upper()


def verify_file(path: Path) -> None:
    size, sha256 = hash_file(path)
    if size != EXPECTED_SIZE_BYTES or sha256 != EXPECTED_SHA256:
        raise ValueError(
            f"Snapshot verification failed for {path}: "
            f"expected {EXPECTED_SIZE_BYTES} bytes and SHA-256 "
            f"{EXPECTED_SHA256}; found {size} bytes and {sha256}."
        )


def main() -> None:
    TARGET_FILE.parent.mkdir(parents=True, exist_ok=True)
    if TARGET_FILE.exists():
        verify_file(TARGET_FILE)
        print(f"Verified existing snapshot: {TARGET_FILE}")
        return

    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            prefix=".food.parquet.",
            suffix=".download",
            dir=TARGET_FILE.parent,
            delete=False,
        ) as temporary_file:
            temporary_path = Path(temporary_file.name)
            digest = hashlib.sha256()
            size = 0
            request = urllib.request.Request(
                SNAPSHOT_URL,
                headers={"User-Agent": "indonesia-food-product-landscape/1.0"},
            )
            with urllib.request.urlopen(request, timeout=60) as response:
                while chunk := response.read(CHUNK_SIZE_BYTES):
                    temporary_file.write(chunk)
                    size += len(chunk)
                    digest.update(chunk)
            temporary_file.flush()
            os.fsync(temporary_file.fileno())

        sha256 = digest.hexdigest().upper()
        if size != EXPECTED_SIZE_BYTES or sha256 != EXPECTED_SHA256:
            raise ValueError(
                "Downloaded snapshot verification failed: "
                f"expected {EXPECTED_SIZE_BYTES} bytes and SHA-256 "
                f"{EXPECTED_SHA256}; found {size} bytes and {sha256}."
            )
        temporary_path.replace(TARGET_FILE)
        print(f"Downloaded and verified snapshot commit {SNAPSHOT_COMMIT}.")
        print(f"Snapshot: {TARGET_FILE}")
    finally:
        if temporary_path is not None and temporary_path.exists():
            temporary_path.unlink()


if __name__ == "__main__":
    main()
