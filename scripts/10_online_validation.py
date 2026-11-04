import csv
import hashlib
import http.client
import html
import json
import re
import socket
import ssl
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from html.parser import HTMLParser
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_FILE = PROJECT_ROOT / "data" / "raw" / "food.parquet"
DATASET_COLUMNS_FILE = PROJECT_ROOT / "outputs" / "profiling" / "dataset_columns.csv"
TAXONOMY_FILE = (
    PROJECT_ROOT / "data" / "reference" / "off_categories_taxonomy_2026-10-25.json"
)
TAXONOMY_CHECK_FILE = (
    PROJECT_ROOT / "outputs" / "profiling" / "nonfood_scope_taxonomy_check.csv"
)
OUTPUT_DIR = PROJECT_ROOT / "outputs" / "profiling"

EXPECTED_LOCAL_SHA256 = (
    "DA39B2C5AAF1F85B2E637B904B5FC3A29780DD7E184254F4B660CFE0CD84999A"
)
EXPECTED_LOCAL_SIZE = 7_975_461_945
REPOSITORY = "openfoodfacts/product-database"
HF_API_ROOT = "https://huggingface.co/api/datasets"
USER_AGENT = "Global-Product-Brand-Landscape-Research/1.0"
RETRIEVED_ON = date.today().isoformat()
NETWORK_ERRORS = (
    HTTPError,
    URLError,
    TimeoutError,
    socket.timeout,
    ssl.SSLError,
    http.client.HTTPException,
)

SEEDS = {
    "V1_FAQ": "https://wiki.openfoodfacts.org/Talk:FAQs",
    "V1_SUPPORT": (
        "https://support.openfoodfacts.org/help/en-gb/21-manage-my-products/"
        "53-can-animal-products-non-food-products-cosmetics-and-other-products-"
        "be-integrated-into-open-food-facts"
    ),
    "V2": (
        "https://openfoodfacts.github.io/documentation/docs/Product-Opener/api/"
        "tutorials/scanning-cosmetics-pet-food-and-other-products/"
    ),
    "V3": "https://github.com/openfoodfacts/openfoodfacts-server/issues/11330",
    "V4": "https://huggingface.co/datasets/openfoodfacts/product-database",
    "V5": (
        "https://world.openproductsfacts.org/facets/categories/"
        "Open%20Food%20Facts"
    ),
}

LOG_COLUMNS = [
    "claim_id",
    "claim",
    "source_url",
    "source_type",
    "retrieved_on",
    "result",
    "evidence_note",
    "notes",
]
COMMIT_COLUMNS = [
    "commit_id",
    "committed_date",
    "food_parquet_size_bytes",
    "food_parquet_sha256",
    "matches_local",
    "retrieved_on",
]


class TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.skip_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"script", "style", "noscript", "svg"}:
            self.skip_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "noscript", "svg"} and self.skip_depth:
            self.skip_depth -= 1
        elif tag in {"p", "div", "li", "tr", "h1", "h2", "h3", "br"}:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if not self.skip_depth:
            self.parts.append(data)


def fetch_bytes(url: str, timeout: int = 30) -> tuple[bytes, str]:
    request = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(request, timeout=timeout) as response:
        return response.read(), response.headers.get_content_charset() or "utf-8"


def page_text(payload: bytes, charset: str) -> str:
    source = payload.decode(charset, errors="replace")
    parser = TextExtractor()
    parser.feed(source)
    return html.unescape("\n".join(parser.parts))


def network_error(error: Exception) -> str:
    if isinstance(error, HTTPError):
        return f"HTTP {error.code}: {error.reason}"
    if isinstance(error, URLError):
        return f"network error: {error.reason}"
    if isinstance(error, (TimeoutError, socket.timeout)):
        return f"network error: {error}"
    return f"request error: {error}"


def make_log(
    claim_id: str,
    claim: str,
    source_url: str,
    source_type: str,
    result: str,
    evidence_note: str,
    notes: str = "",
) -> dict[str, str]:
    if len(evidence_note.split()) > 25:
        raise ValueError(f"Evidence note for {claim_id} exceeds 25 words.")
    return {
        "claim_id": claim_id,
        "claim": claim,
        "source_url": source_url,
        "source_type": source_type,
        "retrieved_on": RETRIEVED_ON,
        "result": result,
        "evidence_note": evidence_note,
        "notes": notes,
    }


def local_file_identity() -> tuple[int, str]:
    if not DATA_FILE.is_file():
        raise FileNotFoundError(f"Local Parquet file not found: {DATA_FILE}")
    size = DATA_FILE.stat().st_size
    digest = hashlib.sha256()
    with DATA_FILE.open("rb") as source:
        for block in iter(lambda: source.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return size, digest.hexdigest().upper()


def api_json(url: str) -> object:
    payload, charset = fetch_bytes(url)
    return json.loads(payload.decode(charset))


def list_hf_commits() -> tuple[list[dict], str]:
    url = f"{HF_API_ROOT}/{REPOSITORY}/commits/main?limit=1000"
    try:
        response = api_json(url)
    except NETWORK_ERRORS as error:
        return [], network_error(error)
    if not isinstance(response, list):
        return [], "not verified: unexpected Hugging Face commits response"
    commits = [entry for entry in response if isinstance(entry, dict)]
    if not commits:
        return [], "not verified: no commit history returned"
    if len(commits) >= 1_000:
        return commits, (
            "not verified: commit listing reached the 1,000-entry API limit; "
            "history may be incomplete"
        )
    oldest_title = str(commits[-1].get("title") or "").casefold()
    oldest_message = str(commits[-1].get("message") or "").casefold()
    if "squash" in oldest_title or "squash" in oldest_message:
        return commits, (
            "history boundary is a squash commit; earlier repository history "
            "is unavailable in the listing"
        )
    return commits, ""


def food_metadata_for_commit(commit_id: str) -> tuple[int | str, str]:
    url = (
        f"{HF_API_ROOT}/{REPOSITORY}/tree/{commit_id}"
        "?recursive=true&expand=true"
    )
    response = api_json(url)
    if not isinstance(response, list):
        return "", ""
    files = [
        entry
        for entry in response
        if isinstance(entry, dict)
        and str(entry.get("path", "")).split("/")[-1] == "food.parquet"
    ]
    if not files:
        return "", ""
    files.sort(key=lambda entry: (entry.get("path") != "food.parquet", entry.get("path", "")))
    metadata = files[0]
    size = metadata.get("size", "")
    lfs = metadata.get("lfs") or {}
    sha = str(lfs.get("oid") or metadata.get("oid") or "")
    if sha.startswith("sha256:"):
        sha = sha.removeprefix("sha256:")
    return size, sha.upper()


def upstream_commit_audit(local_sha256: str) -> tuple[pd.DataFrame, str]:
    commits, history_error = list_hf_commits()
    def inspect_commit(commit: dict) -> tuple[dict[str, str], str]:
        commit_id = str(commit.get("commitId") or commit.get("id") or "")
        committed_date = (
            commit.get("createdAt")
            or commit.get("created_at")
            or commit.get("date")
            or ""
        )
        try:
            size, sha = food_metadata_for_commit(commit_id)
        except NETWORK_ERRORS as error:
            size, sha = "", ""
            return (
                {
                    "commit_id": commit_id,
                    "committed_date": committed_date,
                    "food_parquet_size_bytes": size,
                    "food_parquet_sha256": sha,
                    "matches_local": "N",
                    "retrieved_on": RETRIEVED_ON,
                },
                network_error(error),
            )
        return (
            {
                "commit_id": commit_id,
                "committed_date": committed_date,
                "food_parquet_size_bytes": size,
                "food_parquet_sha256": sha,
                "matches_local": (
                    "Y" if sha and sha == local_sha256 else "N"
                ),
                "retrieved_on": RETRIEVED_ON,
            },
            "",
        )

    with ThreadPoolExecutor(max_workers=4) as executor:
        inspected = list(executor.map(inspect_commit, commits))
    rows = [row for row, _ in inspected]
    metadata_errors = [error for _, error in inspected if error]
    if metadata_errors:
        history_error = history_error or (
            "metadata unavailable for one or more commits: "
            + "; ".join(sorted(set(metadata_errors)))
        )
    if rows:
        result = pd.DataFrame(rows, columns=COMMIT_COLUMNS)
    else:
        result = pd.DataFrame(columns=COMMIT_COLUMNS)
    return result, history_error


def validate_claims(
    local_sha256: str,
    local_size: int,
    history_error: str,
) -> list[dict[str, str]]:
    logs: list[dict[str, str]] = []
    identity_matches = (
        local_size == EXPECTED_LOCAL_SIZE and local_sha256 == EXPECTED_LOCAL_SHA256
    )
    logs.append(
        make_log(
            "H0",
            "Local food.parquet identity matches the recorded size and SHA-256.",
            "data/raw/food.parquet",
            "secondary",
            "supported" if identity_matches else "contradicted",
            (
                f"Local file is {local_size} bytes with SHA-256 {local_sha256}."
            ),
            "Expected size/hash "
            f"{EXPECTED_LOCAL_SIZE}/{EXPECTED_LOCAL_SHA256}; "
            f"history status: {history_error or 'retrieved'}",
        )
    )

    faq_results = []
    for claim_id, url in (
        ("V1_FAQ", SEEDS["V1_FAQ"]),
        ("V1_SUPPORT", SEEDS["V1_SUPPORT"]),
    ):
        claim = (
            "Contributors flag non-food products with categories so moderators "
            "can move them to a sister project."
        )
        try:
            payload, charset = fetch_bytes(url)
            text = page_text(payload, charset)
            normalized = text.casefold()
            relevant = (
                "non-food" in normalized
                or "non food" in normalized
                or "non-alimentaire" in normalized
            )
            category_signal = "categor" in normalized or "tag" in normalized
            move_signal = (
                "moderator" in normalized
                or "move" in normalized
                or "transfer" in normalized
            )
            if relevant and category_signal and move_signal:
                result = "supported"
                note = "Page describes non-food categorization and moderator transfer to another project."
            elif relevant and (category_signal or move_signal):
                result = "partially_supported"
                note = "Page mentions non-food products, but only part of the flagging and transfer workflow."
            else:
                result = "not_verified"
                note = "Fetched page did not establish the complete contributor-flag and moderator-transfer claim."
            faq_results.append(result)
            logs.append(
                make_log(
                    claim_id,
                    claim,
                    url,
                    "primary",
                    result,
                    note,
                    "Evidence checked only on the supplied seed page.",
                )
            )
        except NETWORK_ERRORS as error:
            faq_results.append("not_verified")
            logs.append(
                make_log(
                    claim_id,
                    claim,
                    url,
                    "primary",
                    "not_verified",
                    "Seed page could not be retrieved, so the claim was not verified.",
                    network_error(error),
                )
            )

    try:
        payload, charset = fetch_bytes(SEEDS["V2"])
        text = page_text(payload, charset)
        normalized = text.casefold()
        has_field = "product_type" in normalized
        values_found = all(
            re.search(rf"\b{re.escape(value)}\b", normalized)
            for value in ("beauty", "food", "petfood", "product")
        )
        v2_result = "supported" if has_field and values_found else "partially_supported"
        v2_note = (
            "Tutorial lists product_type values beauty, food, petfood, and product."
            if has_field and values_found
            else "Tutorial retrieved, but the complete field/value set was not found."
        )
        v2_notes = "Values are cited as stated by the supplied official tutorial."
    except NETWORK_ERRORS as error:
        v2_result = "not_verified"
        v2_note = "Seed page could not be retrieved, so the claim was not verified."
        v2_notes = network_error(error)
    logs.append(
        make_log(
            "V2",
            "Open Food Facts documents product_type values beauty, food, petfood, and product.",
            SEEDS["V2"],
            "primary",
            v2_result,
            v2_note,
            v2_notes,
        )
    )

    if DATASET_COLUMNS_FILE.is_file():
        columns = pd.read_csv(DATASET_COLUMNS_FILE, dtype=str)
        column_names = columns["column_name"].fillna("").tolist()
        product_type_columns = [
            name for name in column_names if "product_type" in name.casefold()
        ]
        local_result = "contradicted" if product_type_columns else "supported"
        local_note = (
            "Column inventory contains product_type-like fields: "
            + ", ".join(product_type_columns)
            if product_type_columns
            else "Column inventory contains no product_type-like field among 111 Parquet columns."
        )
        local_notes = f"Checked {DATASET_COLUMNS_FILE.relative_to(PROJECT_ROOT)}."
    else:
        local_result = "not_verified"
        local_note = "Local dataset column inventory is unavailable."
        local_notes = str(DATASET_COLUMNS_FILE)
    logs.append(
        make_log(
            "V2_LOCAL",
            "The local Parquet schema has no product_type-like column.",
            "local file: outputs/profiling/dataset_columns.csv",
            "secondary",
            local_result,
            local_note,
            local_notes,
        )
    )

    try:
        raw_issue, charset = fetch_bytes(SEEDS["V3"])
        issue_text = page_text(raw_issue, charset)
        issue_lower = issue_text.casefold()
        issue_date_match = re.search(
            rb'"createdAt"\s*:\s*"([^"]+)',
            raw_issue,
            flags=re.IGNORECASE,
        )
        if issue_date_match is None:
            issue_date_match = re.search(
                rb'<relative-time[^>]+datetime=["\']([^"\']+)["\']',
                raw_issue,
                flags=re.IGNORECASE,
            )
        issue_date = (
            issue_date_match.group(1).decode("ascii", errors="replace")
            if issue_date_match
            else ""
        )
        exact_count = re.search(r"\b12,?566\b", issue_text)
        approximate_count = re.search(r"\b12k\b", issue_text, flags=re.IGNORECASE)
        beauty_signal = "beauty" in issue_lower
        if exact_count and approximate_count and beauty_signal and issue_date:
            v3_result = "supported"
            v3_note = (
                f"Issue reports about 12k beauty-type records, gives 12,566, "
                f"and is dated {issue_date[:10]}."
            )
        elif beauty_signal and (exact_count or approximate_count):
            v3_result = "partially_supported"
            count_note = "12,566" if exact_count else "about 12k"
            date_note = f"; date {issue_date[:10]}" if issue_date else "; date not verified"
            v3_note = f"Issue mentions {count_note} beauty-type records{date_note}."
        else:
            v3_result = "not_verified"
            v3_note = "Fetched issue did not expose the stated beauty-product counts and date."
        v3_notes = f"Exact count found: {bool(exact_count)}; approximate count found: {bool(approximate_count)}; issue date: {issue_date or 'not verified'}."
    except NETWORK_ERRORS as error:
        v3_result = "not_verified"
        v3_note = "Seed issue could not be retrieved, so the claim was not verified."
        v3_notes = network_error(error)
    logs.append(
        make_log(
            "V3",
            "GitHub issue #11330 reports beauty-type products in the food database; capture its counts and date.",
            SEEDS["V3"],
            "primary",
            v3_result,
            v3_note,
            v3_notes,
        )
    )

    try:
        payload, charset = fetch_bytes(SEEDS["V4"])
        card_text = page_text(payload, charset)
        normalized = card_text.casefold()
        split_mentions = "beauty" in normalized and "food" in normalized
        production_mentions = any(
            term in normalized for term in ("pyarrow", "jsonl", "daily dump")
        )
        criterion_mentions = any(
            phrase in normalized
            for phrase in (
                "split criterion",
                "criteria for the split",
                "separated based on",
                "split based on",
                "criterion used to split",
            )
        )
        if split_mentions and production_mentions and criterion_mentions:
            v4_result = "supported"
            v4_note = "Card describes food/beauty splits, Parquet production, and a split criterion."
        elif split_mentions and production_mentions:
            v4_result = "partially_supported"
            v4_note = "Card describes food/beauty splits and Parquet production; split criterion is not documented."
        else:
            v4_result = "partially_supported" if split_mentions or production_mentions else "not_verified"
            v4_note = "Fetched card exposes only part, or none, of the stated split and production details."
        v4_notes = (
            f"Split mention={split_mentions}; production mention={production_mentions}; "
            f"explicit criterion mention={criterion_mentions}."
        )
    except NETWORK_ERRORS as error:
        v4_result = "not_verified"
        v4_note = "Seed dataset card could not be retrieved, so the claim was not verified."
        v4_notes = network_error(error)
    logs.append(
        make_log(
            "V4",
            "Dataset card describes food and beauty splits and Parquet production; verify whether split criterion is documented.",
            SEEDS["V4"],
            "primary",
            v4_result,
            v4_note,
            v4_notes,
        )
    )

    local_taxonomy_note = "Pinned-taxonomy cross-reference unavailable."
    try:
        if not TAXONOMY_CHECK_FILE.is_file():
            raise FileNotFoundError(str(TAXONOMY_CHECK_FILE))
        taxonomy_check = pd.read_csv(TAXONOMY_CHECK_FILE, dtype=str, keep_default_na=False)
        taxonomy_rows = taxonomy_check.set_index("tag").to_dict(orient="index")
        targets = (
            "en:incorrect-product-type",
            "en:open-food-facts",
            "en:non-open-products-facts",
        )
        local_status = {
            tag: taxonomy_rows.get(tag, {}).get("exists_as_exact_node", "not_checked")
            for tag in targets
        }
        local_taxonomy_note = (
            "Pinned taxonomy exact-node status: "
            + "; ".join(f"{tag}={status}" for tag, status in local_status.items())
            + "."
        )
        payload, charset = fetch_bytes(SEEDS["V5"])
        website_text = page_text(payload, charset).casefold()
        website_claim = (
            "open food facts" in website_text
            and "incorrect product type" in website_text
            and "non open products facts" in website_text
        )
        if website_claim:
            disagreements = any(status != "Y" for status in local_status.values())
            v5_result = (
                "partially_supported" if disagreements else "supported"
            )
            v5_note = (
                "Website shows the category relationships; local taxonomy "
                + ("differs on exact-node presence." if disagreements else "contains both exact nodes.")
            )
        else:
            v5_result = "not_verified"
            v5_note = "Fetched category page did not expose the claimed category relationships."
        v5_notes = local_taxonomy_note
    except FileNotFoundError as error:
        v5_result = "not_verified"
        v5_note = "Online category claim or local taxonomy comparison could not be verified."
        v5_notes = str(error)
    except NETWORK_ERRORS as error:
        v5_result = "not_verified"
        v5_note = "Category page could not be retrieved, so the website claim was not verified."
        v5_notes = f"{network_error(error)} {local_taxonomy_note}"
    logs.append(
        make_log(
            "V5",
            "Open Products Facts category page places Open Food Facts under Incorrect product type and Non open products facts.",
            SEEDS["V5"],
            "primary",
            v5_result,
            v5_note,
            v5_notes,
        )
    )

    if history_error:
        logs.append(
            make_log(
                "HF_HISTORY",
                "The listed Hugging Face commit history covers all earlier repository revisions.",
                f"{HF_API_ROOT}/{REPOSITORY}/commits/main",
                "primary",
                "not_verified",
                "Earlier repository history or complete file metadata could not be verified.",
                history_error,
            )
        )
    return logs


def write_csv(path: Path, rows: list[dict[str, str]], columns: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as output:
        writer = csv.DictWriter(
            output,
            fieldnames=columns,
            extrasaction="ignore",
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    local_size, local_sha256 = local_file_identity()
    identity_matches = (
        local_size == EXPECTED_LOCAL_SIZE and local_sha256 == EXPECTED_LOCAL_SHA256
    )
    if not identity_matches:
        print(
            "MISMATCH: local Parquet identity differs from the recorded size/hash: "
            f"{local_size} bytes, SHA-256 {local_sha256}."
        )
    commits, history_error = upstream_commit_audit(local_sha256)
    commit_path = OUTPUT_DIR / "online_validation_hf_commits.csv"
    commits.to_csv(
        commit_path,
        index=False,
        encoding="utf-8",
        lineterminator="\n",
        na_rep="",
    )

    logs = validate_claims(local_sha256, local_size, history_error)
    write_csv(
        OUTPUT_DIR / "online_validation_log.csv",
        logs,
        LOG_COLUMNS,
    )

    matching_commits = commits.loc[
        commits["food_parquet_sha256"].eq(local_sha256)
        & commits["food_parquet_sha256"].ne("")
    ]
    if history_error and matching_commits.empty and "squash commit" in history_error:
        commit_result = "no match among available history; earlier history unavailable"
    elif history_error and matching_commits.empty:
        commit_result = "not available"
    elif matching_commits.empty:
        commit_result = "no match"
    else:
        commit_result = ", ".join(matching_commits["commit_id"].tolist())
    print(f"Local file size: {local_size:,} bytes")
    print(f"Local SHA-256: {local_sha256}")
    print(f"Hugging Face commit result: {commit_result}")
    print(f"HF history note: {history_error or 'complete metadata retrieved'}")
    print(f"Online validation rows: {len(logs)}")
    print("Validation result counts:")
    print(pd.Series([row["result"] for row in logs]).value_counts().to_string())
    print(f"Outputs saved: {commit_path.name}, online_validation_log.csv")


if __name__ == "__main__":
    main()
