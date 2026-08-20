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
| `{{PROCEDURE_EXAMPLE}}` | The profile's headline surgery, used as the Genie/demo example | `knee replacement` (adult) · `tonsillectomy` (pediatric) |
| `{{PROCEDURE_CODE}}` | Its procedure code | `27447` (adult) · `42820` (pediatric) |

**Profile-specific** (set these to match the `profile` you generate — the surgical example must exist
in the data): the `adult` profile uses `knee replacement` = `27447`; the `pediatric` profile uses
`tonsillectomy` = `42820`. (Asking Genie about a procedure that isn't in the chosen profile returns
nothing — that's why these are tokens, not hardcoded.) Baseline outcome rates also differ by profile
(see `lab_guides/workshop_assets.md`).

Each attendee **creates their own** ETL schema **`{{CATALOG}}.analyst101_<user>`** (not a token) as
the first step of the ETL lab — self-serve, not pre-provisioned. The only setup is a one-time
`CREATE SCHEMA` grant on `{{CATALOG}}` to the workshop group. This assumes the workshop runs in the
customer's own workspace, where attendees already have identities.

## Quick instantiate (find/replace)

From the repo root, after copying it to a client working dir:

```bash
CLIENT="Acme Health"; CATALOG="acme_analyst101"; SCHEMA="analyst101_shared"
WS="adb-<workspace-id>.<n>.azuredatabricks.net"; FLAVOR="healthcare encounters (synthetic, no PHI)"
# profile-specific — adult: PROC_EX="knee replacement"; PROC_CODE="27447"
PROC_EX="tonsillectomy"; PROC_CODE="42820"    # pediatric
grep -rl '{{' . --include='*.md' --include='*.json' --include='*.py' | while read f; do
  sed -i '' \
    -e "s|{{CLIENT_NAME}}|$CLIENT|g" -e "s|{{CATALOG}}|$CATALOG|g" \
    -e "s|{{SCHEMA}}|$SCHEMA|g"      -e "s|{{WORKSPACE_URL}}|$WS|g" \
    -e "s|{{INDUSTRY_FLAVOR}}|$FLAVOR|g" \
    -e "s|{{PROCEDURE_EXAMPLE}}|$PROC_EX|g" -e "s|{{PROCEDURE_CODE}}|$PROC_CODE|g" "$f"
done
```

Keep the tokenized master clean — instantiate into a **copy** (or a `clients/<name>/` overlay).
Client overlays hold customer-identifying values (names, workspace URLs), so keep them **out of any
public repo** — this repo git-ignores `clients/`.

## Per-client setup checklist

1. **Fill tokens** (above) in your client copy.
2. **Generate the shared dataset** — run `data_generation/generate_workshop_data.py` with widgets
   `catalog={{CATALOG}}`, `schema={{SCHEMA}}`, and **`profile`** (`adult` or `pediatric`) on
   serverless. Builds the star schema + PCP-continuity enrichment + comments + PK/FKs. (Run it in
   a Databricks Git folder so it can import `profiles/`.)
3. **Grant the workshop group** — `USE CATALOG` + `CREATE SCHEMA` on `{{CATALOG}}` and `USE SCHEMA` +
   `SELECT` on `{{CATALOG}}.{{SCHEMA}}`. Attendees create + own their own `{{CATALOG}}.analyst101_<user>`
   schema in the lab (no per-attendee provisioning). See `lab_guides/workshop_assets.md` for the SQL.
4. **Stage the ETL file** — share the profile's `etl_lab/facilities_raw.<profile>.csv` with
   attendees (or pre-stage it in a shared volume via the generator's optional `stage_raw_csv` cell).
   If you changed a profile's facilities, regenerate with `python etl_lab/build_raw_csv.py --all`.
5. **Import the dashboard** — `dashboard/workshop.lvdash.json` (already retargeted to
   `{{CATALOG}}.{{SCHEMA}}` by the find/replace). Confirm widgets render.
6. **Create the Genie space** — follow `genie/genie_space_config.md` on the star-schema tables.
7. **Smoke test** — run one Designer build end-to-end (12 clean rows + lineage) and ask Genie one
   question.
8. **(Optional) Advanced module** — for a Databricks Day / advanced follow-on on the *same*
   dataset, run `advanced_module/continuity_assets.sql` (metric view + SQL functions + enriched
   view for PCP continuity) and register them as Genie trusted assets. See `advanced_module/README.md`.

## What to customize per audience
- **Population:** pick `adult` or `pediatric` via the `profile` widget. To add another population
  or vertical, copy `profiles/pediatric.py` to a new module, edit its seed lists, register it in
  `profiles/__init__.py`, and run `python etl_lab/build_raw_csv.py --profile <name>`. The generator,
  ETL lab, and advanced module all pick it up unchanged — no code edits elsewhere.
- **ETL target table:** the lab builds `dim_facility` (small, relatable). The raw CSV is generated
  from the profile's facility list, so changing a profile's facilities automatically updates the lab.
- **Tableau cheat-sheet:** the AI/BI workbook keeps an optional Tableau↔AI/BI translation callout.
  Leave it in for Tableau shops; drop it otherwise.
