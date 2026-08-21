# Instantiating this template

This repo is a **reusable Analyst 101 workshop template**. Setup is **notebook-driven** — there is no
find/replace step and no CLI. You add the repo as a Databricks **Git folder**, open one setup
notebook, fill a few widgets, and run it. The notebook builds the shared dataset, the advanced
module, the dashboard, and the Genie Agent, then grants the attendees and smoke-tests the result.

## One-time setup (per workshop workspace)

1. **Add this repo as a Git folder** — in the target workspace, **Workspace → Create → Git folder →**
   `https://github.com/realboom/analyst101-workshop.git`.
2. **Open** `notebooks/00_setup_workshop.py` and attach it to **serverless**.
3. **Run Step 0a** to create the input widgets, fill them in at the top (table below), then run
   **Step 0b** and **Steps 1–6 one at a time**. That's the whole build — no local tools, no tokens to
   hand-edit, no CLI. (The Databricks SDK is auto-authenticated inside the notebook.)

The notebook does all of it: generates the star schema for the chosen profile, builds the advanced
module (metric view + SQL functions), imports + publishes the AI/BI dashboard, creates the Genie
space with trusted assets, grants the attendee group, and runs a verification smoke test.

## Setup-notebook widgets

| Widget | What it is | Example |
|---|---|---|
| `catalog` | Unity Catalog catalog for the workshop (created if missing) | `acme_analyst101` |
| `schema` | Shared schema for the pre-built star schema (AI/BI half) | `analyst101_shared` |
| `profile` | Population flavor — `adult` (acute care) or `pediatric` (children's health) | `pediatric` |
| `client_name` | *Optional* display name appended to the deployed dashboard/Genie names | `Acme Health` |
| `procedure_example` | The profile's headline surgery, used as the Genie/demo example | `tonsillectomy` |
| `procedure_code` | Its procedure code (**must exist in the chosen profile**) | `42820` |
| `warehouse_id` | SQL warehouse id (blank = auto-pick a serverless warehouse) | |
| `attendee_group` | Attendee group name **or** comma-separated emails (must already exist) | `analyst101_attendees` |

**Profile ↔ procedure must match:** the `adult` profile uses `knee replacement` = `27447`; the
`pediatric` profile uses `tonsillectomy` = `42820`. Asking Genie about a procedure that isn't in the
chosen profile returns nothing — that's why these are widgets, not hardcoded. Baseline outcome rates
also differ by profile (see `workshop_assets.md`). The notebook warns if the profile and
procedure code don't line up.

Each attendee **creates their own** ETL schema **`<catalog>.analyst101_<user>`** as the first step of
the ETL lab — self-serve, not pre-provisioned. The setup notebook's grant step gives the attendee
group `USE CATALOG` + `CREATE SCHEMA` on the catalog and `USE SCHEMA` + `SELECT` on the shared schema.
This assumes the workshop runs in the customer's own workspace, where attendees already have identities.

## Attendee-facing guides

The lab guides (`attendee_workbook.md`, `instructor_guide.md`, `genie/genie_space_config.md`) are
human-readable docs that still carry `{{CATALOG}}` / `{{SCHEMA}}` / `{{PROCEDURE_EXAMPLE}}` /
`{{PROCEDURE_CODE}}` / `{{WORKSPACE_URL}}` / `{{INDUSTRY_FLAVOR}}` placeholders — the setup notebook
builds the *assets*, not these docs. When you
hand the guides to attendees, fill those placeholders with your workshop's real values (a filled
Google Doc per client works well). Keep customer-identifying values in a `clients/<name>/` overlay,
which is git-ignored and stays out of this public repo.

## What to customize per audience
- **Population:** pick `adult` or `pediatric` via the `profile` widget. To add another population or
  vertical, copy `profiles/pediatric.py` to a new module, edit its seed lists, register it in
  `profiles/__init__.py`, and run `python etl_lab/build_raw_csv.py --profile <name>` to regenerate its
  ETL raw CSV. The generator, ETL lab, and advanced module all pick it up unchanged — no code edits
  elsewhere.
- **ETL target table:** the lab builds `dim_facility` (small, relatable). The raw CSV is generated
  from the profile's facility list, so changing a profile's facilities automatically updates the lab.
- **Tableau cheat-sheet:** the AI/BI workbook keeps an optional Tableau↔AI/BI translation callout.
  Leave it in for Tableau shops; drop it otherwise.

## Advanced module (Databricks Day / advanced follow-on)
For a deeper session on the *same* dataset, the setup notebook already deploys
`advanced_module/continuity_assets.sql` (metric view + SQL functions + enriched view for PCP
continuity) and registers them as Genie trusted assets. See `advanced_module/README.md` for the
talk track.
