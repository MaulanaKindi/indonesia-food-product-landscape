## Country Landscape Metrics

**Metric:** Recorded product records by country

**Definition:** Number of distinct dataset records assigned to each selected country tag, calculated using `COUNT(DISTINCT record_id)`.

**Unit:** Dataset records.

**Country selection:** Thirteen explicitly mapped country tags. Non-country labels such as `en:world` and `en:worldwide` are excluded.

**Multi-country handling:** A record assigned to multiple countries is counted once in each applicable country. Therefore, country-level totals overlap and must not be summed to estimate the number of globally unique products.

**Sensitivity check:** Compare record counts with distinct non-empty product codes. Repeated codes are not automatically deduplicated because records sharing a code may have different attributes.

**Interpretation limit:** These figures describe product records documented in Open Food Facts, not total products sold, market size, sales volume, brand market share, or consumer demand. Differences between countries may reflect both underlying product coverage and differences in database contribution and completeness.

**Scope limitation:** The analysis includes thirteen selected countries. It is not an exhaustive or statistically representative comparison of all countries.
