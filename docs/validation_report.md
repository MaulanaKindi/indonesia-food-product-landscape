## Country Record Count Sensitivity Check

**Objective:** Assess whether country-level record counts materially change when counting distinct valid product codes instead of distinct dataset records.

**Method:** Compare `COUNT(DISTINCT record_id)` with `COUNT(DISTINCT code)` after excluding null and empty codes, for the thirteen selected country tags.

**Results:** The country rankings remain unchanged. Four countries show differences between record counts and distinct valid codes: France (28), United States (3), United Kingdom (2), and the remaining difference of 0 for all other selected countries except as reported in the query output. Germany, Japan, India, Singapore, Thailand, Philippines, Indonesia, Malaysia, China, and Vietnam have identical counts.

**Conclusion:** The sensitivity check does not materially affect the comparative ranking of the selected countries.

**Limitation:** This comparison is a robustness check, not proof of product-level uniqueness. Records sharing a code may contain different attributes, and a code may be associated with more than one country tag.
