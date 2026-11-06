# 01 Data Source

## Dataset

Open Food Facts Product Database

## Source

https://huggingface.co/datasets/openfoodfacts/product-database

The Hugging Face dataset card describes its Parquet files as simplified conversions of Open Food Facts daily JSONL dumps, processed with PyArrow. It notes that debug, hierarchy, and interface-language (`lc`) tags were removed while product tags were retained. The local Parquet file is therefore a transformed dataset snapshot, not the original unmodified JSONL dump.

## Local File

data/raw/food.parquet

## Reproducible Snapshot

| Item | Status |
|----------|----------|
| Pinned Hugging Face dataset commit | `31f31c441274c095718cc88ae582030a5a615415` |
| Snapshot file | `food.parquet` |
| Local file format | Parquet |
| Expected size | 7,975,461,945 bytes |
| Expected SHA-256 | `DA39B2C5AAF1F85B2E637B904B5FC3A29780DD7E184254F4B660CFE0CD84999A` |
| Local artifact verification | Size and SHA-256 checked on 2026-11-04 |

The project uses the immutable commit and file checksum as its reproducibility contract. `scripts/00_download_snapshot.py` downloads that exact revision and verifies both values before placing the file at `data/raw/food.parquet`; the database builder verifies them again. The verified file profile is 4,828,207 rows and 111 columns. The local retrieval event is not part of the reproducibility claim.

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

The 2026-11-04 check of the current Open Food Facts reuse terms states ODbL for the database, DbCL for individual contents, and CC BY-SA for product images, and requires attribution/linking to Open Food Facts and compliance with applicable derivative-work conditions. This project does not use product images. The current Hugging Face dataset card/API also labels the repository with `agpl-3.0` and `odbl`, but does not clarify whether AGPL applies to the dataset artifact, conversion code, or both.

For the scoped portfolio publication, the project authorizes reviewed aggregate Stage 5/6 results and a narrowly scoped, AI-assisted semantic audit of a fixed 150-record Indonesian sample plus an eight-record Meat & poultry census. A source-based online follow-up of the 48 disputed or uncertain sample records is published as an evidence log, with Open Food Facts attribution and links to applicable terms. These are diagnostics, not independent human validation or ground truth; online checks are targeted and non-random. The repository does not redistribute the source Parquet, DuckDB databases, the unlabeled local human-review sample, general record-level extracts, or the pinned taxonomy. These audit files are a specific record-level exception to the aggregate-only publication scope; they remain subject to applicable source-license conditions. The project does not claim that MIT applies to data-derived outputs, nor does it make a legal determination about whether an output is a Produced Work or Derivative Database, or what the Hugging Face AGPL label covers. This is a documented publication policy, not legal advice; seek qualified advice for a definitive legal classification or materially different reuse.

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

## Provenance and Publication Disclosure

The source is identified by the immutable commit above, and the local artifact's size and SHA-256 matched on 2026-11-04. That pin and checksum, rather than a historical file-acquisition event, define reproducibility. The public repository excludes the raw Parquet, DuckDB databases, the unlabeled local human-review sample, general record-level extracts, and pinned taxonomy JSON. It includes a reviewed allowlist of aggregate Stage 5/6 tables and validation reports, plus the fixed-sample AI-assisted audit and its targeted online evidence log described above. Open Food Facts attribution and links to its terms appear in the README and this note. The project-authored code uses MIT as documented in the repository LICENSE; that license does not apply to source data or data-derived outputs.
