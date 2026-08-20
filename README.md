# Analyst 101 Workshop — a reusable Databricks fundamentals workshop

A hands-on, **client-agnostic Analyst 101 workshop** that walks a customer from a **raw file** all the
way to a **natural-language answer** — one continuous story on a realistic synthetic dataset
({{INDUSTRY_FLAVOR}}).

Two halves, one dataset:

1. **Foundations + ETL** — attendees create a Unity Catalog **volume**, upload a messy CSV, and
   use the no-code **Lakeflow Designer** visual ETL builder to build a **bronze → silver → gold**
   medallion pipeline that produces a governed `dim_facility` table.
2. **AI/BI** — attendees build an **AI/BI dashboard** and stand up a **Genie** space on the
   pre-built star schema, so they see governed tables turn into interactive analytics and
   plain-language Q&A.

An optional **[advanced module](advanced_module/)** (Metric Views, SQL functions, trusted assets
for Genie) runs on the *same* shared dataset — designed so a follow-on **Databricks Day / advanced
session** reuses exactly the data analysts built in the workshop. One dataset, two sessions.

> This template started from Kiara Koeppen's excellent SelectHealth AI/BI workshop
> (`kiara-koeppen/selecthealth-aibi-workshop`) — the synthetic dataset, starter dashboard, Genie
> config, and AI/BI lab guides are hers. This version generalizes it into a reusable Analyst 101 and
> adds the volume-upload + Lakeflow Designer medallion front-half.

## How to use it

This is a **template**. Fill the placeholder tokens (`{{CLIENT_NAME}}`, `{{CATALOG}}`, …) for your
account, then provision and deploy. See **[`TEMPLATE.md`](TEMPLATE.md)** for tokens and the
per-client setup checklist. Instantiate into a `clients/<name>/` overlay — those hold
customer-identifying values, so they're kept **out of this public repo** (`clients/` is git-ignored).

**Pick a population profile.** The dataset comes in flavors — `adult` (acute care) and `pediatric`
(children's health) — selected by the generator's `profile` widget. A profile
([`profiles/`](profiles/)) is the single source of truth for its facilities, diagnoses,
procedures, specialties, and ages; the generator **and** the ETL-lab raw CSV both derive from it,
so they never drift. Add a vertical by dropping in a new profile module.

## Data flow

```
facilities_raw.<profile>.csv ──upload──► UC Volume ──Lakeflow Designer──►  bronze ─► silver ─► gold
   (messy source extract)      ({{CATALOG}}.analyst101_<user>.landing)         dim_facility
                                                                              │
   generate_workshop_data.py ─────► {{CATALOG}}.{{SCHEMA}} star schema ◄──────┘ (same shape)
     (fact_encounters + dim_provider, dim_facility, dim_diagnosis,
      dim_procedure, dim_patient, dim_visit_type)
                                             │
                     ┌───────────────────────┼───────────────────────┐
                     ▼                        ▼                        ▼
              AI/BI Dashboard           Genie Space          advanced_module/
                                                        (Metric View + SQL functions,
                                                         PCP continuity → Databricks Day)
```

The ETL lab builds `dim_facility` into each attendee's **own sandbox schema**; the AI/BI half and
the advanced module run on the **shared, pre-built star schema** (the full 80k-row dataset). The
generator enriches it with `dim_patient` (assigned PCP) + `dim_visit_type` so the advanced module's
PCP-continuity metric is meaningful.

## What's in here

```
analyst101-workshop/
├── README.md                     · this file
├── TEMPLATE.md                   · placeholder tokens + per-client instantiate checklist
├── profiles/                     · population "flavor packs" — single source of truth per dataset
│   ├── common.py                 · shared name pools, visit types, US-state map, messiness recipe
│   ├── adult.py                  · adult / acute-care seed data
│   └── pediatric.py              · pediatric / children's-health seed data
├── data_generation/
│   └── generate_workshop_data.py · parameterized synthetic dataset (picks a profile via widget)
├── etl_lab/                      · the Foundations + ETL front-half
│   ├── build_raw_csv.py          · generates each profile's messy CSV (no drift from the dataset)
│   ├── facilities_raw.adult.csv  · messy source extract (adult) — derived from profiles/adult
│   ├── facilities_raw.pediatric.csv · messy source extract (pediatric)
│   ├── etl_lab_guide.md          · attendee steps (volume → Designer bronze→silver→gold)
│   └── etl_instructor_notes.md   · talk track, timings, UC grants, gotchas
├── dashboard/workshop.lvdash.json· starter AI/BI (Lakeview) dashboard
├── genie/genie_space_config.md   · Genie space setup: instructions + sample questions
├── advanced_module/              · optional "go deeper" layer (Databricks Day / advanced session)
│   ├── continuity_assets.sql     · metric view + SQL functions + enriched view (PCP continuity)
│   └── README.md                 · deploy steps + demo talk track (Metric Views, functions, Genie)
├── lab_guides/
│   ├── agenda.md                 · full Analyst 101 agenda (Foundations+ETL, then AI/BI)
│   ├── instructor_guide.md       · AI/BI facilitator manual
│   ├── attendee_workbook.md      · AI/BI step-by-step for attendees
│   └── workshop_assets.md        · live links/IDs + provisioning checklist
└── clients/                      · per-client overlays (git-ignored; kept out of the public repo)
```

## Prerequisites

- A Databricks workspace with **Unity Catalog** and **serverless** compute.
- Attendee accounts with a **sandbox schema** each (`{{CATALOG}}.analyst101_<user>`) and the grants in
  `TEMPLATE.md`, plus SELECT on the shared star schema.
- Databricks CLI authenticated if you deploy from the CLI.
