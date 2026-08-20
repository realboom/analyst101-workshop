# ETL Lab — Instructor Notes

**The lab:** `etl_lab/etl_lab_guide.md`. Attendees create a volume, upload their profile's `facilities_raw.<profile>.csv`,
and build a no-code **bronze → silver → gold** pipeline in **Lakeflow Designer** that lands a
clean `dim_facility`. This is the Analyst 101 foundations front-half; the AI/BI half follows on the
pre-built shared star schema.

**Time budget:** ~45–55 min. Concepts 5 · Volume + upload 8 · Bronze 7 · Silver 15 ·
Gold 10 · Verify/lineage 8.

---

## The one thing to land
Data quality work is real work, and Databricks lets an analyst do it **visually, governed, and
repeatable** — not in a throwaway spreadsheet. Every messy thing in the file maps to one
Designer operator. By the end they have a lineage graph and a table they could schedule nightly.

## Cadence: "watch me, then you do it"
Designer is new to most attendees. Demo Steps 3–4 (start a build, add the bronze source) live on
the projector once, then let them do it. Do Silver (Step 5) **together, operator by operator**,
pausing on each live preview so they see the change. Gold (Step 6) they can mostly drive
themselves; float and help.

## What each messy element teaches (and the operator that fixes it)
| In the raw file | Layer | Designer operator |
|---|---|---|
| Leading/trailing spaces on names | Silver | Trim / clean |
| `State` as full name / code / mixed case (e.g. "Utah" / "UT " / "ut") | Silver | Upper + map to 2-letter (standard US-state lookup) |
| `Type` in mixed casing (e.g. "pediatric clinic" / "PEDIATRIC CLINIC") | Silver | Title-case |
| Trailing blank line | Silver | Filter `Facility ID` not null |
| One duplicated facility row | Silver | Deduplicate on `facility_id` |
| Blank `Region` on two facilities (each shares a City with a sibling) | Gold | Fill from same-city sibling (window by `City`) |
| `Facility ID` → `facility_id` etc. | Gold | Rename to snake_case |

**Order matters — call it out:** standardize *before* you dedupe, or the duplicated rows won't
match. This is a genuine ETL lesson, not a Databricks quirk.

**Expected end state:** exactly **12 rows**, clean 2-letter states, proper-cased types, no null
regions. (Validated per profile: `python etl_lab/build_raw_csv.py --all --check` proves the
documented transforms reproduce each profile's star-schema `dim_facility`.)

## Prerequisites BEFORE the session (one-time, group-level)
- **Serverless compute** available in the workspace (Designer runs on serverless).
- The workshop group has, on `{{CATALOG}}`: `USE CATALOG` + **`CREATE SCHEMA`** (so each attendee
  can create their own schema in the lab), and `USE SCHEMA` + `SELECT` on the shared schema
  `{{CATALOG}}.{{SCHEMA}}`. Attendees **create their own** `{{CATALOG}}.analyst101_<user>` schema as
  ETL Step 1 — they own it, so `CREATE VOLUME` / `CREATE TABLE` on it come automatically. No
  per-attendee schema provisioning by the instructor.
- Attendees can reach **Lakeflow / Designer** (Data Engineering entitlement).
- The profile's `facilities_raw.<profile>.csv` shared with attendees (Slack/email/repo link), OR
  pre-staged in a shared volume they can copy from. The data generator has an optional
  `stage_raw_csv` cell that writes the matching profile's file to a volume as a backup.

## Common gotchas
- **"I can't create a schema"** → the workshop group is missing `CREATE SCHEMA` on `{{CATALOG}}`.
  Fix: `GRANT CREATE SCHEMA ON CATALOG {{CATALOG}} TO \`analyst101_attendees\`;` (then they re-run
  `CREATE SCHEMA {{CATALOG}}.analyst101_<their-name>`).
- **"I don't see Create Volume / can't create a table"** → almost always they're pointed at a schema
  they don't own (e.g. the shared one). Confirm they're in **their own** `analyst101_<user>` schema,
  which they created and therefore own outright.
- **"Designer won't start / no compute"** → serverless not enabled or not selected.
- **Source parsed as one column** → header/delimiter detection; re-open the source pane and
  confirm comma-delimited with header row.
- **Dedup left 13 rows** → they deduped *before* standardizing; the duplicated rows still differ
  by case/whitespace. Reorder: clean → standardize → dedupe.
- **Region still blank after gold** → the same-city sibling fill ran on the *untrimmed* City (so
  the two rows didn't match as the same city); trim City first, then partition by City.

## If you're short on time
Drop the optional PK/comments (Step 7.3) and the standalone silver materialization — a single
Designer flow (bronze source → transforms → gold output) is enough to tell the whole story. Do
**not** skip the lineage view; it's the payoff shot.

## The bridge to the AI/BI half
Close with: *"The `dim_facility` you just built is the same kind of governed table the dashboards
and Genie read. Now let's go use tables like it."* Then move to `attendee_workbook.md`.
