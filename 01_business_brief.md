# Business Brief: Global Product and Brand Landscape

## 1. Project Overview

**Project:** Global Product and Brand Landscape Analysis  
**Target Role:** Market Intelligence Analyst  
**Data Source:** Open Food Facts  
**Tools:** Kaggle Notebooks, DuckDB, SQL, GitHub

This project analyzes the structure of recorded food products and brands across countries and product categories. It combines relational database design, data quality assessment, SQL analysis, and business interpretation to demonstrate practical Market Intelligence capabilities.

## 2. Business Objective

Develop a structured view of the product and brand landscape represented in Open Food Facts to identify differences in recorded product variety, brand distribution, and brand concentration across selected countries and categories.

The analysis aims to demonstrate how publicly available product-level data can support exploratory competitive and category intelligence, while explicitly acknowledging the limits of the dataset.

## 3. Primary Business Question

How does the recorded landscape of food products and brands differ across countries and product categories?

## 4. Supporting Questions

1. Which product categories contain the greatest recorded variety of products and brands?
2. How are recorded products distributed across brands within selected categories, and how concentrated is that distribution?
3. How does Indonesia's recorded product landscape compare with selected countries that have sufficient and reasonably comparable data?

## 5. Analytical Scope

- Assess data completeness, consistency, duplication, and suitability for cross-country comparison.
- Design a relational database schema based on the source data and analytical requirements.
- Use SQL for aggregation, joins, CTEs, and window functions where they provide genuine analytical value.
- Compare selected countries and categories using clearly defined metrics.
- Translate defensible findings into concise business insights and recommendations for further investigation.

The final geographic and category scope will be determined after data profiling.

## 6. Data and Measurement Principles

- Product counts represent records in Open Food Facts, not total products sold in a market.
- Recorded brand counts do not establish market share or commercial dominance.
- Brand concentration calculated from product records is not equivalent to sales concentration.
- Country coverage, missing values, duplicate records, and classification inconsistencies may affect comparisons.
- All cleaning and exclusion decisions must be documented and justified.

## 7. Expected Deliverables

- Business brief and project README.
- Reproducible SQL scripts for profiling, cleaning, schema creation, and analysis.
- Relational schema and entity-relationship diagram.
- Data quality log documenting key issues and decisions.
- Analytical results with clearly defined metrics.
- Business findings, limitations, and recommendations for further investigation.

## 8. Definition of Done

The project is complete when:

1. The data source, extraction method, and relevant licensing and attribution requirements are documented.
2. The relational schema is justified by the data and analytical requirements.
3. SQL scripts can be executed in the documented order, subject to stated environment and data prerequisites.
4. Important data quality decisions are traceable.
5. Key analytical results can be reproduced and independently checked.
6. Business conclusions are supported by the results and distinguish observations from interpretations.
7. The GitHub repository is understandable to a reviewer unfamiliar with the project.
