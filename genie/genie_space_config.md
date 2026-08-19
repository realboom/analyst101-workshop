# Genie Space - {{CLIENT_NAME}} Workshop

In the workshop, each analyst stands up a Genie space **from their own published dashboard**
(see the handbooks, Day 1 Genie segment), then pastes in the instructions below and asks a few
questions. The point is to show how little it takes to get a good Genie space when the data is
well documented, and how it connects to the AI/BI dashboard they just built.

There is also a **pre-built standalone Genie space as a backup** (in case the live publish hiccups):
- Build it on the five tables: `{{CATALOG}}.{{SCHEMA}}.{fact_encounters, dim_provider, dim_facility, dim_diagnosis, dim_procedure}`.
- Record the space ID in `lab_guides/workshop_assets.md` once created, so both groups reuse it.

## Why this works with so few instructions
The dataset ships fully documented: every table has a description, every column has a comment, and
primary/foreign keys are defined. Genie uses the comments to understand fields and the foreign keys
to join tables automatically, so you mostly just need to pin down metric definitions and conventions.

## Paste this into the Genie space "Instructions"
```
This Genie space answers questions about synthetic hospital encounters. There is no PHI.

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
- "knee replacement" means primary_procedure_code = '27447'.
- Round rates to one decimal place and currency to whole dollars.
```

## Sample questions to add (and to ask live)
1. How many encounters were there in 2024 by region?
2. Which 10 providers have the highest 30-day readmission rate, with at least 200 encounters?
3. What is the average length of stay for a knee replacement?
4. Show the monthly encounter volume trend for the last 2 years.
5. Which facilities have the highest complication rate?
6. Compare mortality rate by clinical category.
7. What is the average total paid per encounter by payer type?

## Verified
On the documented dataset, Genie correctly auto-joined `fact_encounters` to `dim_facility` using the
foreign key and answered "which facility has the highest 30-day readmission rate (min 500 encounters)"
without any join hints. Knee-replacement length of stay returns about 2.27 days.

## Facilitator tips
- Let a more **skeptical attendee** drive, and always click **Show generated code** so they see the
  Databricks SQL behind each answer — great for anyone who wants SQL-dialect help.
- Point out that the good answers come largely from the **table/column comments and the foreign keys**,
  plus the short instructions block, not from heavy configuration.
- If an answer looks off, use **Fix it** / the feedback flow (Yes / Fix it / Request review) to show
  the human-in-the-loop trust model rather than a black box.
