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

## The context Genie reads — prefer SQL over free text
The dataset ships fully documented (table + column comments, PK/FKs), so Genie already understands the
fields and can join the tables. Layer a little curated context on top — and per Databricks' guidance
(the Databricks Day slide 8–9 story), **SQL-based context beats free-text instructions.** Add these,
in priority order:

### 1. General instructions (keep it short)
Scope + conventions only — metrics move to SQL expressions, and the procedure name resolves from the
data itself. Paste into **Instructions**:
```
This Genie Agent answers questions about synthetic hospital encounters. There is no PHI.

Data model:
- fact_encounters is the central fact table, one row per patient encounter.
- Join to dim_provider on provider_id, dim_facility on facility_id,
  dim_diagnosis on primary_icd10_code = icd10_code, and dim_procedure on
  primary_procedure_code = procedure_code.

Conventions:
- Express all rates as a percentage from 0 to 100, rounded to one decimal; currency as whole dollars.
- When ranking providers or facilities by a rate, only include those with at least 200 encounters
  unless the user asks otherwise.
- Show plain-language names in results (provider_name, facility_name, region, clinical_category,
  procedure_description), not the id columns.
```

### 2. Column synonyms (map user words to the schema)
Add as **synonyms** on the relevant column/table, so everyday language resolves:
- **visit**, **visits** → encounter (`fact_encounters`) — *the classic: the table is "encounters," analysts say "visits"*
- **doctor**, **physician** → provider (`dim_provider`)
- **hospital**, **clinic**, **site** → facility (`dim_facility`)

*(Don't synonym every procedure name to a code — unmaintainable. Genie already matches "tonsillectomy"
to `procedure_description` in `dim_procedure`.)*

### 3. SQL expressions (define metrics + filters once)
Add as **SQL expressions** — reusable, governed definitions Genie applies consistently:

| Name | Type | Expression |
|---|---|---|
| `readmission_rate` | measure | `AVG(readmitted_30d) * 100` |
| `complication_rate` | measure | `AVG(complication_flag) * 100` |
| `mortality_rate` | measure | `AVG(mortality_flag) * 100` |
| `avg_los` | measure | `AVG(length_of_stay_days)` |
| `inpatient_only` | filter | `encounter_type = 'Inpatient'` |

### 4. Example SQL query (teach a full, validated answer)
Add one **example query** — it teaches the join, the rate-as-percentage convention, and the ≥200
threshold in one validated sample:

Question: *"30-day readmission rate by facility, for facilities with at least 200 encounters"*
```sql
SELECT f.facility_name,
       ROUND(AVG(e.readmitted_30d) * 100, 1) AS readmit_rate_pct,
       COUNT(*) AS encounters
FROM fact_encounters e
JOIN dim_facility f USING (facility_id)
GROUP BY f.facility_name
HAVING COUNT(*) >= 200
ORDER BY readmit_rate_pct DESC
```

## Sample questions to ask live
1. How many encounters (visits) were there in 2024 by region?
2. Which 10 providers have the highest 30-day readmission rate, with at least 200 encounters?
3. What is the average length of stay for a {{PROCEDURE_EXAMPLE}}?
4. Show the monthly visit volume trend for the last 2 years.
5. Which facilities have the highest complication rate?
6. Compare mortality rate by clinical category.

## Verified
On the documented dataset, Genie correctly auto-joined `fact_encounters` to `dim_facility` using the
foreign key and answered "which facility has the highest 30-day readmission rate (min 500 encounters)"
without any join hints. The profile's headline surgery (`{{PROCEDURE_EXAMPLE}}`) returns a sensible length of stay (e.g. tonsillectomy ≈ 2.4 days on the pediatric profile).

## Facilitator tips
- Let a more **skeptical attendee** drive, and always click **Show generated code** so they see the
  Databricks SQL behind each answer — great for anyone who wants SQL-dialect help.
- Point out that the good answers come from the **setup**: table/column comments + keys, a few
  **SQL expressions** (metrics/filters), an **example query**, and **synonyms** — SQL-based context,
  not a long free-text prompt. That's the Databricks Day "the setup drives the answer" thesis.
- If an answer looks off, use **Fix it** / the feedback flow (Yes / Fix it / Request review) to show
  the human-in-the-loop trust model rather than a black box.
