# Genie Agent — Analyst 101 Workshop

> **Naming:** "Genie spaces" are now **Genie Agents** in the UI (create via the **Genie Agents**
> sidebar → **New**). The API endpoint is still `/api/2.0/genie/spaces`.

In the workshop, each analyst stands up a **Genie Agent** (Genie Agents → New → select tables →
Create; **Genie Code** launches to configure it), then pastes in the instructions below and asks a
few questions. The point is to show how little it takes to get a good agent when the data is well
documented, and how it connects to the AI/BI dashboard they just built. *(A published dashboard's
**Ask Genie** box is a quick embedded ask on that dashboard's data — handy, but not the full agent.)*

**Loop-closing detail (live attendee flow):** each attendee selects shared `fact_encounters` +
`dim_provider` + `dim_diagnosis` + `dim_procedure`, but uses **their own
`{{CATALOG}}.analyst101_<user>.dim_facility`** (the table they built in Part 0) in place of the shared
`dim_facility`. It carries the same `facility_id`s, so it joins to `fact_encounters` on the key named
in the instructions below — no auto-FK needed. Facility/region questions then answer off the analyst's
own governed table. (If an attendee's ETL build failed, fall back to the shared `dim_facility`.)

The setup notebook builds this as a **pre-built standalone Genie Agent** (backup + Databricks Day
driver):
- Build it on the five tables: `{{CATALOG}}.{{SCHEMA}}.{fact_encounters, dim_provider, dim_facility, dim_diagnosis, dim_procedure}`.
- Record the agent ID in `../workshop_assets.md` once created, so both groups reuse it.

## Why this works with so few instructions
The dataset ships fully documented: every table has a description, every column has a comment, and
primary/foreign keys are defined. Genie uses the comments to understand fields and the foreign keys
to join tables automatically, so you mostly just need to pin down metric definitions and conventions.

## Paste this into the agent's "Instructions"
```
This Genie Agent answers questions about synthetic hospital encounters. There is no PHI.

Data model:
- fact_encounters is the central fact table, one row per patient encounter.
- Join to dim_provider on provider_id, dim_facility on facility_id,
  dim_diagnosis on primary_icd10_code = icd10_code, and dim_procedure on
  primary_procedure_code = procedure_code. (These foreign keys are already defined.)

Metric definitions (express all rates as a percentage from 0 to 100):
- Readmission rate = AVG(readmitted_30d) * 100
- Mortality rate = AVG(mortality_flag) * 100
- Complication rate = AVG(complication_flag) * 100
- Average length of stay = AVG(length_of_stay_days), in days

Conventions:
- When ranking providers or facilities by a rate, only include those with at least
  200 encounters unless the user asks otherwise.
- Show plain-language names in results (provider_name, facility_name, region,
  clinical_category, procedure_description), not the id columns.
- "{{PROCEDURE_EXAMPLE}}" means primary_procedure_code = '{{PROCEDURE_CODE}}'.
- Round rates to one decimal place and currency to whole dollars.
```

## Sample questions to add (and to ask live)
1. How many encounters were there in 2024 by region?
2. Which 10 providers have the highest 30-day readmission rate, with at least 200 encounters?
3. What is the average length of stay for a {{PROCEDURE_EXAMPLE}}?
4. Show the monthly encounter volume trend for the last 2 years.
5. Which facilities have the highest complication rate?
6. Compare mortality rate by clinical category.
7. What is the average total paid per encounter by payer type?

## Verified
On the documented dataset, Genie correctly auto-joined `fact_encounters` to `dim_facility` using the
foreign key and answered "which facility has the highest 30-day readmission rate (min 500 encounters)"
without any join hints. The profile's headline surgery (`{{PROCEDURE_EXAMPLE}}`) returns a sensible length of stay (e.g. tonsillectomy ≈ 2.4 days on the pediatric profile).

## Facilitator tips
- Let a more **skeptical attendee** drive, and always click **Show generated code** so they see the
  Databricks SQL behind each answer — great for anyone who wants SQL-dialect help.
- Point out that the good answers come largely from the **table/column comments and the foreign keys**,
  plus the short instructions block, not from heavy configuration.
- If an answer looks off, use **Fix it** / the feedback flow (Yes / Fix it / Request review) to show
  the human-in-the-loop trust model rather than a black box.
