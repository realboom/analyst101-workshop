# Advanced module — Metric Views, SQL functions, and trusted assets for Genie

The "go deeper" layer for a **Databricks Day / advanced session**, built on the **same shared
encounters dataset** as the Analyst 101 workshop (`{{CATALOG}}.{{SCHEMA}}`). One dataset, two
sessions: analysts *build* the data in Analyst 101 (raw file → medallion → star schema →
dashboard/Genie), then come back and see governed metrics, callable SQL functions, and accurate
Genie on data they already recognize.

## The story: PCP continuity of care

**Continuity** = the share of a patient's *standard* visits where the attending provider is the
patient's **assigned PCP**. It's a real quality measure, and it's a clean way to show three
capabilities on one metric:

- **Metric View** — `pcp_continuity_metrics` defines the ratio **once**, in YAML, governed by
  Unity Catalog. Every dashboard, notebook, and Genie Agent computes it identically. No more
  "whose number is right?"
- **SQL functions** — `pcp_continuity_ratio(...)`, `standard_visit_count(...)`, and the table
  function `pcp_continuity_by_provider(...)` package the logic so anyone (including Genie) can
  call it with a date window / facility instead of re-deriving joins.
- **Trusted assets → Genie accuracy** — register the metric view and functions as **trusted
  assets** in a Genie Agent so plain-language questions resolve to the governed definitions, not
  ad-hoc SQL. This is the accuracy story: the answer is right *because* the definition is governed.

## Prerequisites

The PCP-continuity enrichment must exist in the shared schema — it's produced by
`data_generation/generate_workshop_data.py` (adds `dim_patient.assigned_pcp_id`,
`dim_provider.is_pcp`, and biases attending-provider assignment so the ratio is realistic and varies
by facility, ~55–90%). Standard visits are `visit_type_id = 'OFFICE'` — the rule lives in the governed
assets (`encounters_enriched` / metric view / functions), not as a flag on `dim_visit_type`.

## Deploy

1. Run the generator into `{{CATALOG}}.{{SCHEMA}}` (see `../TEMPLATE.md`).
2. Run `continuity_assets.sql` top-to-bottom on a serverless SQL warehouse (instantiate the
   `{{TOKEN}}`s first, or run it from a client copy). It creates the enriched view, the metric
   view, and the three SQL functions.
3. Smoke-test:
   ```sql
   SELECT {{CATALOG}}.{{SCHEMA}}.pcp_continuity_ratio();                     -- overall ratio
   SELECT * FROM {{CATALOG}}.{{SCHEMA}}.pcp_continuity_by_provider()
     ORDER BY continuity_ratio DESC;                                          -- rank providers
   SELECT `Facility`, MEASURE(`PCP Continuity Ratio`)                         -- metric view
     FROM {{CATALOG}}.{{SCHEMA}}.pcp_continuity_metrics GROUP BY `Facility`;   -- measures need MEASURE()
   ```
4. In a Genie Agent over `{{CATALOG}}.{{SCHEMA}}`, add the metric view and the functions as
   **trusted assets / example SQL** (see `../genie/genie_space_config.md` for the base agent).
   Then ask: *"What's our PCP continuity rate?"*, *"Which providers have the lowest continuity
   with at least 200 standard visits?"*, *"Show continuity by facility by month."*

## Demo talk track (maps to the deck)

1. **Metric View** — open `pcp_continuity_metrics`, show the YAML: the ratio is defined once.
2. **SQL function** — call `pcp_continuity_ratio('2025-01-01','2025-12-31')`; note anyone can reuse it.
3. **Trusted assets** — show the same question answered in Genie, resolving to the governed asset.
4. **Accuracy** — click **Show generated code**; the SQL uses the trusted definition, so the
   number matches the dashboard and the metric view exactly.
