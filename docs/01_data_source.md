# 01 Data Source

## Dataset

Open Food Facts Product Database

## Source

https://huggingface.co/datasets/openfoodfacts/product-database

The Hugging Face dataset card describes its Parquet files as simplified conversions of Open Food Facts daily JSONL dumps, processed with PyArrow. It notes that debug, hierarchy, and interface-language (`lc`) tags were removed while product tags were retained. The local Parquet file is therefore a transformed dataset snapshot, not the original unmodified JSONL dump.

## Local File

data/raw/food.parquet

## Source Snapshot and Extraction

| Item | Status |
|----------|----------|
| Exact upstream commit, release, or snapshot date | The local file hash matches the `food.parquet` metadata in three listed Hub commits; the originating commit and local retrieval date are not determined |
| Hub metadata retrieval date | 2026-10-26 |
| Local file retrieval date | Not yet recorded |
| Extraction/download method and parameters | Not yet recorded |
| Local file format | Parquet |
| Current local file size | 7,975,461,945 bytes |
| Local file SHA-256 checksum | `DA39B2C5AAF1F85B2E637B904B5FC3A29780DD7E184254F4B660CFE0CD84999A` |

The local file's observed profile is 4,828,207 rows and 111 columns. These counts and the file size identify the current local artifact only; they do not identify its upstream release.

On 2026-10-29, a bounded audit of project documentation, scripts, and outputs found no contemporaneous record establishing the local download date or extraction method. Windows currently reports a file last-write timestamp of 2026-10-23 14:43:35 local time; this filesystem metadata is not accepted as proof of download or retrieval time because it can change when files are copied or restored. No user-level browser history or download cache was inspected. The retrieval date and method therefore remain unknown; do not infer them from the timestamp.

### Upstream Snapshot Check

On 2026-10-26, the Hugging Face Hub commit listing exposed metadata for 683 commits. The local file's size and SHA-256 match the `food.parquet` metadata in these three listed commits:

| Commit | Commit date |
|----------|----------|
| `31f31c441274c095718cc88ae582030a5a615415` | 2026-10-23 |
| `0273016bf1a86da29ccb1b22a487574f0c9a31ea` | 2026-10-23 |
| `99d7ba5bcb35b693300108f43cfaeee508b7e915` | 2026-10-22 |

This verifies a content-hash match to the listed Hub metadata, but does not establish which commit was used to retrieve the local file: the same file hash appears in multiple commits, and earlier history is unavailable beyond a squash boundary. The local retrieval date and extraction method remain not determined. The check used Hub metadata and did not download the Parquet file.

On 2026-11-04, the local artifact was rechecked: 7,975,461,945 bytes and SHA-256 `DA39B2C5AAF1F85B2E637B904B5FC3A29780DD7E184254F4B660CFE0CD84999A`. The Hugging Face dataset API reported current `main` commit `e5ed2fae58c2ce58d26a1298f61c7d40b1bd1e4a` (last modified 2026-11-04 08:01 UTC); its current `food.parquet` metadata reports 8,029,922,066 bytes and SHA-256 `84D9D985BB1262EE1F8B71770ADA9ADA2F87F0B40B8A37BC99917111FB0E95E6`. Thus the current upstream file is not the local pinned artifact. The local source remains pinned and unchanged; do not silently replace it with current `main`.

The three October commits above are reproducible content matches for the local bytes. They can identify commits that contain the same file, but cannot establish which one was actually used to retrieve it. The exact local retrieval event/date and whether the file was downloaded from a particular commit or extracted from another copy remain unknown. The local timestamp remains filesystem metadata only, not retrieval evidence. No user-level browser/download history was inspected.

### Online Claim Validation

The evidence log is `outputs/profiling/online_validation_log.csv`; commit metadata is in `outputs/profiling/online_validation_hf_commits.csv`. On 2026-10-26, the supplied official tutorial documented `product_type` values `beauty`, `food`, `petfood`, and `product`. The local 111-column inventory contains no `product_type`-like field. GitHub issue #11330, dated 2025-02-06, reports about 12,000 beauty-type records and gives an exact count of 12,566; this is an issue statement, not a count verified against this local snapshot.

The Hugging Face dataset card describes food and beauty splits and the Parquet production process, but the split criterion was not documented on the inspected card. The Open Products Facts category page supports the stated category relationship, while the pinned taxonomy has no exact nodes for `en:open-food-facts` or `en:non-open-products-facts`; the website and local taxonomy therefore do not fully agree. The two supplied contributor-flag sources did not verify the complete claim: the FAQ evidence was inconclusive, and the support page could not be retrieved because its TLS certificate had expired. The nine-row evidence log contains 4 supported, 2 partially supported, and 3 not-verified results; none was contradicted. These claims are not treated as established facts unless the evidence log supports them.

## Category Taxonomy Reference

The Parquet dataset retains `categories_tags` but its dataset card states that hierarchy fields were removed. To inspect parent-child relationships, the project saved a copy of the Open Food Facts category taxonomy from:

- Source: https://static.openfoodfacts.org/data/taxonomies/categories.json
- Local snapshot: `data/reference/off_categories_taxonomy_2026-10-25.json`
- Retrieved: 2026-10-25
- File size: 4,703,948 bytes
- SHA-256: `EB03AEFABAE4C6269B5FBC3E89160F8DA84CA3300A53787E27EAB5FE2D1020D5`
- Taxonomy nodes in the saved file: 14,774

The source Parquet upstream release date is unknown, so this current taxonomy snapshot cannot be assumed to be contemporaneous with the product data. The category audit records exact tag matches and unmatched tags; it does not silently infer aliases. Recheck the taxonomy license, version, and attribution conditions before redistributing it or derivative taxonomy data.

## Licensing and Attribution

The Open Food Facts terms of reuse state that the database is under the Open Database License (ODbL 1.0), individual database contents are under the Database Contents License (DbCL 1.0), and product images are under CC BY-SA 3.0. They require attribution to Open Food Facts and sharing derivative works under the applicable license conditions. This project analyzes product data and does not currently use product images.

The Hugging Face dataset card's machine-readable metadata lists both `AGPL-3.0` and `ODbL`; its prose describes the database and individual-content licenses above. The AGPL metadata's applicability to the Parquet data versus accompanying code is not established by the card alone and should be clarified before redistribution. This note records the source statements, not legal advice.

Before publishing or redistributing the dataset or substantial derived extracts, review the current license texts and attribution/share-alike requirements for the specific use.

Terms initially checked: 2026-10-25. Rechecked: 2026-11-04.

- [Hugging Face dataset card and README](https://huggingface.co/datasets/openfoodfacts/product-database)
- [Open Food Facts terms of reuse](https://world.openfoodfacts.org/terms-of-use)
- [Open Database License 1.0](https://opendatacommons.org/licenses/odbl/1-0/)
- [Database Contents License 1.0](https://opendatacommons.org/licenses/dbcl/1.0/)
- [Creative Commons Attribution-ShareAlike 3.0](https://creativecommons.org/licenses/by-sa/3.0/)

The 2026-11-04 check of the current Open Food Facts reuse terms still states ODbL for the database, DbCL for individual contents, and CC BY-SA for product images, and requires attribution/linking to Open Food Facts and sharing derivative works under applicable license conditions. This project currently does not use product images. The current Hugging Face dataset card/API still labels the repository with both `agpl-3.0` and `odbl`; the card prose describes the Open Food Facts database/content licenses but does not clarify whether AGPL applies to the dataset artifact, the conversion code, or both. Do not infer a license for this project’s own code from that metadata. The owner selected MIT for original project code only; it does not apply to Open Food Facts data, third-party reference files, or data-derived results. The intended treatment of data/database derivatives remains subject to the applicable source terms and is not a legal determination.

## ISO 3166-1 Reference

`data/reference/iso_3166_alpha2.csv` is the project's validation snapshot for two-letter ISO 3166-1 codes. It is derived from the IANA tzdata `iso3166.tab` reference, whose header identifies the codes as current as of ISO/TC 46 N1127 (2024-02-29) and states that the file is public domain. The reference file is used to validate approved country mappings; its source and effective date should be revisited when the mapping is refreshed.

## Purpose

This dataset is the primary source for the Indonesia Food Product Landscape project.

## Initial Dataset Profile

| Metric | Value |
|----------|----------|
| Rows | 4,828,207 |
| Columns | 111 |

## Notes

The dataset contains product-level records and includes information related to brands, categories, countries, ingredients, and product metadata.

Further profiling and quality assessment are documented separately.

## Provenance Items to Complete

Before final reproducibility review, retain the pinned hash and matching upstream content references; record the local retrieval date/method only if new evidence establishes them. The current upstream `main` file is different and must not be substituted silently. The public repository excludes the raw Parquet, DuckDB databases, record-level samples, and pinned taxonomy JSON. It includes a small allowlist of aggregate Stage 5/6 tables and validation reports, with source attribution in the README and this note. Before redistributing the dataset or substantial derived extracts, review the current license texts and attribution/share-alike requirements for the specific use. The project-authored code uses MIT as documented in the repository LICENSE; that license does not apply to source data or third-party materials.