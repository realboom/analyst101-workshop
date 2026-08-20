-- ============================================================================
-- Advanced module: PCP continuity — governed metric view + SQL functions + view
-- ----------------------------------------------------------------------------
-- These are the "go deeper" assets for a Databricks Day / advanced session, built on the SAME
-- shared encounters dataset the Analyst 101 workshop uses ({{CATALOG}}.{{SCHEMA}}). They rely on
-- the PCP-continuity enrichment produced by data_generation/generate_workshop_data.py
-- (dim_patient.assigned_pcp_id, dim_visit_type.is_standard, dim_provider.is_pcp).
--
-- PCP continuity = share of STANDARD visits where the attending provider (fact_encounters.provider_id)
-- is the patient's assigned PCP (dim_patient.assigned_pcp_id). Non-standard visit types are excluded.
--
-- Run top to bottom on a serverless SQL warehouse after the generator has populated the schema.
-- Demonstrates: Metric Views, SQL functions (scalar + table), and trusted assets for Genie.
-- ============================================================================

-- 1) Enriched convenience view: one row per encounter with an is_pcp_match flag ---------------
CREATE OR REPLACE VIEW {{CATALOG}}.{{SCHEMA}}.encounters_enriched
COMMENT 'Curated wide view: one row per encounter joined to patient, provider, facility and visit type, with a PCP-match flag. Convenience layer for dashboards, metric views and Genie.'
AS
SELECT
  e.encounter_id,
  e.admit_date,
  e.facility_id,
  f.facility_name,
  f.region,
  e.visit_type_id,
  vt.visit_type_name,
  vt.is_standard,
  e.patient_id,
  p.home_facility_id,
  p.assigned_pcp_id,
  e.provider_id                    AS attending_provider_id,
  pr.provider_name                 AS attending_provider_name,
  (e.provider_id = p.assigned_pcp_id) AS is_pcp_match
FROM {{CATALOG}}.{{SCHEMA}}.fact_encounters e
JOIN {{CATALOG}}.{{SCHEMA}}.dim_patient     p  ON e.patient_id     = p.patient_id
JOIN {{CATALOG}}.{{SCHEMA}}.dim_visit_type  vt ON e.visit_type_id  = vt.visit_type_id
JOIN {{CATALOG}}.{{SCHEMA}}.dim_facility    f  ON e.facility_id    = f.facility_id
JOIN {{CATALOG}}.{{SCHEMA}}.dim_provider    pr ON e.provider_id    = pr.provider_id;

-- 2) Governed metric view: define the continuity ratio ONCE ----------------------------------
CREATE OR REPLACE VIEW {{CATALOG}}.{{SCHEMA}}.pcp_continuity_metrics
(`Facility`, `Facility Code`, `Region`, `Encounter Month`, `Total Standard Visits`, `PCP Matched Visits`, `PCP Continuity Ratio`)
COMMENT 'Governed PCP continuity metrics over STANDARD visits only. Define the ratio once; every dashboard, notebook, and Genie Space computes it identically.'
WITH METRICS
LANGUAGE YAML
AS $$
version: 0.1
source: {{CATALOG}}.{{SCHEMA}}.encounters_enriched
filter: is_standard = true
dimensions:
  - name: Facility
    expr: facility_name
  - name: Facility Code
    expr: facility_id
  - name: Region
    expr: region
  - name: Encounter Month
    expr: date_trunc('MONTH', admit_date)
measures:
  - name: Total Standard Visits
    expr: COUNT(1)
  - name: PCP Matched Visits
    expr: COUNT_IF(is_pcp_match)
  - name: PCP Continuity Ratio
    expr: TRY_DIVIDE(COUNT_IF(is_pcp_match), COUNT(1))
$$;

-- 3) SQL functions (trusted assets Genie can call) -------------------------------------------

-- Governed continuity ratio for a date window and optional facility.
CREATE OR REPLACE FUNCTION {{CATALOG}}.{{SCHEMA}}.pcp_continuity_ratio(
  p_start STRING DEFAULT '2023-01-01',
  p_end STRING DEFAULT '2025-12-31',
  p_facility STRING DEFAULT NULL)
RETURNS DOUBLE
COMMENT 'Governed PCP continuity ratio: share of STANDARD visits where the attending provider is the patient''s assigned PCP, within the date window and optional facility. Non-standard visit types are excluded.'
RETURN (
  SELECT try_divide(count_if(e.provider_id = pt.assigned_pcp_id), count(*))
  FROM {{CATALOG}}.{{SCHEMA}}.fact_encounters e
  JOIN {{CATALOG}}.{{SCHEMA}}.dim_patient    pt ON e.patient_id    = pt.patient_id
  JOIN {{CATALOG}}.{{SCHEMA}}.dim_visit_type vt ON e.visit_type_id = vt.visit_type_id
  WHERE vt.is_standard
    AND e.admit_date BETWEEN to_date(p_start) AND to_date(p_end)
    AND (p_facility IS NULL OR e.facility_id = p_facility)
);

-- Count of STANDARD visits in the window, optionally one facility.
CREATE OR REPLACE FUNCTION {{CATALOG}}.{{SCHEMA}}.standard_visit_count(
  p_start STRING DEFAULT '2023-01-01',
  p_end STRING DEFAULT '2025-12-31',
  p_facility STRING DEFAULT NULL)
RETURNS BIGINT
COMMENT 'Count of STANDARD visits in the window (non-standard visit types excluded), optionally filtered to one facility.'
RETURN (
  SELECT count(*)
  FROM {{CATALOG}}.{{SCHEMA}}.fact_encounters e
  JOIN {{CATALOG}}.{{SCHEMA}}.dim_visit_type vt ON e.visit_type_id = vt.visit_type_id
  WHERE vt.is_standard
    AND e.admit_date BETWEEN to_date(p_start) AND to_date(p_end)
    AND (p_facility IS NULL OR e.facility_id = p_facility)
);

-- Continuity ratio per attending provider (table function) — use to rank providers.
CREATE OR REPLACE FUNCTION {{CATALOG}}.{{SCHEMA}}.pcp_continuity_by_provider(
  p_start STRING DEFAULT '2023-01-01',
  p_end STRING DEFAULT '2025-12-31')
RETURNS TABLE (attending_provider_id STRING, provider_name STRING, primary_facility_id STRING,
               standard_visits BIGINT, matched_visits BIGINT, continuity_ratio DOUBLE)
COMMENT 'PCP continuity ratio per attending provider over standard visits in the window. Use to rank providers highest/lowest.'
RETURN
  SELECT e.provider_id AS attending_provider_id, pr.provider_name, pr.primary_facility_id,
         count(*) AS standard_visits,
         count_if(e.provider_id = pt.assigned_pcp_id) AS matched_visits,
         try_divide(count_if(e.provider_id = pt.assigned_pcp_id), count(*)) AS continuity_ratio
  FROM {{CATALOG}}.{{SCHEMA}}.fact_encounters e
  JOIN {{CATALOG}}.{{SCHEMA}}.dim_patient    pt ON e.patient_id    = pt.patient_id
  JOIN {{CATALOG}}.{{SCHEMA}}.dim_visit_type vt ON e.visit_type_id = vt.visit_type_id
  JOIN {{CATALOG}}.{{SCHEMA}}.dim_provider   pr ON e.provider_id   = pr.provider_id
  WHERE vt.is_standard AND e.admit_date BETWEEN to_date(p_start) AND to_date(p_end)
  GROUP BY e.provider_id, pr.provider_name, pr.primary_facility_id;

-- ---------------------------------------------------------------------------------------------
-- Quick checks:
--   SELECT {{CATALOG}}.{{SCHEMA}}.pcp_continuity_ratio();                 -- overall ratio
--   SELECT {{CATALOG}}.{{SCHEMA}}.standard_visit_count();                 -- standard visit count
--   SELECT * FROM {{CATALOG}}.{{SCHEMA}}.pcp_continuity_by_provider()
--     ORDER BY continuity_ratio DESC;                                     -- rank providers
--   SELECT `Facility`, MEASURE(`PCP Continuity Ratio`)                    -- metric view: measures
--     FROM {{CATALOG}}.{{SCHEMA}}.pcp_continuity_metrics GROUP BY `Facility`;  -- must be wrapped in MEASURE()
-- ---------------------------------------------------------------------------------------------
