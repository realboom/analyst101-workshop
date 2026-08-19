# Instantiating this template for a client

This repo is a **reusable Analyst 101 workshop template**. It ships with placeholder tokens so you can
stand it up for any account in a few minutes. Fill the tokens, run the generator, stage the ETL
file, import the dashboard, create the Genie space.

## Placeholder tokens

Every client-specific value is written as a `{{TOKEN}}`. Replace them across the repo:

| Token | What it is | Example |
|---|---|---|
| `{{CLIENT_NAME}}` | Display name of the customer | `Acme Health` |
| `{{CATALOG}}` | Unity Catalog catalog for the workshop | `acme_analyst101` |
| `{{SCHEMA}}` | Shared schema for the pre-built star schema (AI/BI half) | `analyst101_shared` |
| `{{WORKSPACE_URL}}` | Workspace host | `adb-<workspace-id>.<n>.azuredatabricks.net` |
| `{{INDUSTRY_FLAVOR}}` | One-line dataset framing | `healthcare encounters (synthetic, no PHI)` |

Per-attendee ETL sandboxes follow the convention **`{{CATALOG}}.analyst101_<user>`** (not a token —
created one per attendee at provisioning time).

## Quick instantiate (find/replace)

From the repo root, after copying it to a client working dir:

```bash
CLIENT="Acme Health"; CATALOG="acme_analyst101"; SCHEMA="analyst101_shared"
WS="adb-<workspace-id>.<n>.azuredatabricks.net"; FLAVOR="healthcare encounters (synthetic, no PHI)"
grep -rl '{{' . --include='*.md' --include='*.json' --include='*.py' | while read f; do
  sed -i '' \
    -e "s|{{CLIENT_NAME}}|$CLIENT|g" -e "s|{{CATALOG}}|$CATALOG|g" \
    -e "s|{{SCHEMA}}|$SCHEMA|g"      -e "s|{{WORKSPACE_URL}}|$WS|g" \
    -e "s|{{INDUSTRY_FLAVOR}}|$FLAVOR|g" "$f"
done
```

Keep the tokenized master clean — instantiate into a **copy** (or a `clients/<name>/` overlay).
Client overlays hold customer-identifying values (names, workspace URLs), so keep them **out of any
public repo** — this repo git-ignores `clients/`.

## Per-client setup checklist

1. **Fill tokens** (above) in your client copy.
2. **Generate the shared dataset** — run `data_generation/generate_workshop_data.py` with widgets
   `catalog={{CATALOG}}`, `schema={{SCHEMA}}` on serverless. Builds the star schema + comments +
   PK/FKs the AI/BI half relies on.
3. **Provision ETL sandboxes** — one schema per attendee `{{CATALOG}}.analyst101_<user>` with
   `USE CATALOG` + (on their schema) `USE SCHEMA`, `CREATE VOLUME`, `CREATE TABLE`.
4. **Stage the ETL file** — share `etl_lab/facilities_raw.csv` with attendees (or pre-stage it in
   a shared volume; the generator has an optional cell to write it).
5. **Import the dashboard** — `dashboard/workshop.lvdash.json` (already retargeted to
   `{{CATALOG}}.{{SCHEMA}}` by the find/replace). Confirm widgets render.
6. **Create the Genie space** — follow `genie/genie_space_config.md` on the five star-schema tables.
7. **Smoke test** — run one Designer build end-to-end (12 clean rows + lineage) and ask Genie one
   question.

## What to customize per audience
- **Industry:** the dataset is synthetic healthcare and works for payers and providers as-is. For
  a non-healthcare account, swap the code lists in the generator (diagnoses/procedures/facilities)
  and `{{INDUSTRY_FLAVOR}}`; the medallion lab and AI/BI flow are industry-agnostic.
- **ETL target table:** the lab builds `dim_facility` (small, relatable). To use a different
  dimension, swap `etl_lab/facilities_raw.csv` and the Step 5–6 transforms in the lab guide.
- **Tableau cheat-sheet:** the AI/BI workbook keeps an optional Tableau↔AI/BI translation callout.
  Leave it in for Tableau shops; drop it otherwise.
