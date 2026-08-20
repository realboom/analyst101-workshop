# {{CLIENT_NAME}} Analyst 101 Workshop — Agenda

**Audience:** analysts and business users, mixed Databricks familiarity.
**Format:** Hands-on, light on theory. Everyone in the workspace doing the clicks.
**Goal:** go end-to-end on Databricks — from a **raw file** to a **governed table** to a
**dashboard and a plain-language answer** — on a realistic synthetic dataset
({{INDUSTRY_FLAVOR}}), so the skills transfer directly to your real data.

> **Data:** we work from a shared synthetic dataset (no PHI): patient encounters with diagnoses,
> procedures, providers, facilities, and outcomes. It's structured to mirror the kind of analysis
> your team does day to day.

> **Two groups, one workshop:** this agenda runs identically for each group. Same data, same labs.

---

## Single-session Analyst 101 (~3h15, two 10-minute breaks)

| Time | Segment | What we'll do |
|---|---|---|
| 0:00–0:15 | **Welcome & orientation** | Goals, a tour of the workspace and Unity Catalog (catalog → schema → table/volume), and the medallion (bronze→silver→gold) idea. |
| 0:15–1:05 | **Foundations + ETL lab** | Create a **volume**, **upload a raw CSV**, and build a **bronze→silver→gold** pipeline in the no-code **Lakeflow Designer** that produces a governed `dim_facility`. *(`etl_lab/etl_lab_guide.md`)* |
| 1:05–1:15 | *Break* | |
| 1:15–2:05 | **AI/BI Dashboard authoring** | Build charts on the shared dataset: aggregate outcomes by provider/facility, trends over time, drill-downs, filters, cross-filtering. *(Workbook, Parts 1–2)* |
| 2:05–2:15 | *Break* | |
| 2:15–2:50 | **AI-assisted authoring + the semantic layer** | Build visuals from a prompt; introduce **metric views** as governed, reusable metric definitions. *(Workbook, Part 3)* |
| 2:50–3:15 | **Ask Genie** | Create a **Genie space** and ask questions in plain language, with the generated SQL shown. Wrap & how this maps to your real data. *(Workbook, Genie segment + `genie/genie_space_config.md`)* |

**Shorter (~2h) variant:** Orientation (10) → ETL lab (45) → Dashboard authoring (45) →
Ask Genie (20). Drop the semantic-layer segment and advanced drill-downs.

**Two-day variant:** if you have more time, split into Day 1 (Foundations + ETL + dashboard
authoring) and Day 2 (build-your-own-scenario + Genie + share-outs). The instructor guide's
segment playbook and the workbook's later parts support this.

---

## What attendees need
- Access to the workshop Databricks workspace, with rights to **create their own schema** in
  `{{CATALOG}}` (they make `{{CATALOG}}.analyst101_<user>` in the first ETL step) and SELECT on the
  shared dataset (`{{CATALOG}}.{{SCHEMA}}`).
- **Serverless** compute available (Lakeflow Designer runs on it).
- That's it — no prep required. Bring curiosity and, optionally, a report you'd like to recreate.

## A note on flexibility
This agenda is a guide, not a script. If a topic sparks interest, lean in; if something lands
quickly, move on. The point is for the team to get hands-on and form a real opinion.
