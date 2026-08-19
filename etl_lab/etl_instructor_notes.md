# ETL Lab — Instructor Notes

**The lab:** `etl_lab/etl_lab_guide.md`. Attendees create a volume, upload `facilities_raw.csv`,
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
| Leading/trailing spaces (`  Wasatch… `, ` Red Rock…`) | Silver | Trim / clean |
| `State` = "Utah" / "UT " / "ut" / "Idaho" / "ID" / "Nevada" | Silver | Upper + case/map to 2-letter |
| `Type` = "inpatient hospital" / "INPATIENT HOSPITAL" | Silver | Title-case |
| Trailing blank line | Silver | Filter `Facility ID` not null |
| Duplicate FAC003 row | Silver | Deduplicate on `facility_id` |
| Blank `Region` on FAC005 (Logan), FAC010 (Provo) | Gold | Derive region from city |
| `Facility ID` → `facility_id` etc. | Gold | Rename to snake_case |

**Order matters — call it out:** standardize *before* you dedupe, or the two FAC003 rows won't
match as duplicates. This is a genuine ETL lesson, not a Databricks quirk.

**Expected end state:** exactly **12 rows**, states in `{UT, ID, NV}`, 5 proper-cased types, no
null regions. (Validated: the documented transforms reproduce the star-schema `dim_facility`.)

## Prerequisites to provision BEFORE the session
- **Serverless compute** available in the workspace (Designer runs on serverless).
- Each attendee has a **sandbox schema** `{{CATALOG}}.analyst101_<user>` and these grants on it:
  `USE CATALOG` on `{{CATALOG}}`, `USE SCHEMA` + `CREATE VOLUME` + `CREATE TABLE` on their schema.
- Attendees can reach **Lakeflow / Designer** (Data Engineering entitlement).
- `facilities_raw.csv` shared with attendees (Slack/email/repo link), OR pre-staged in a shared
  volume they can copy from. The data generator has an optional cell that writes it to a volume
  as a backup — see `data_generation/generate_workshop_data.py`.

## Common gotchas
- **"I don't see Create Volume / can't create a table"** → missing `CREATE VOLUME` / `CREATE TABLE`
  on their schema. Fastest fix: `GRANT ALL PRIVILEGES ON SCHEMA {{CATALOG}}.analyst101_<user> TO <user>;`
- **"Designer won't start / no compute"** → serverless not enabled or not selected.
- **Source parsed as one column** → header/delimiter detection; re-open the source pane and
  confirm comma-delimited with header row.
- **Dedup left 13 rows** → they deduped *before* standardizing; the two FAC003 rows still differ
  by case/whitespace. Reorder: clean → standardize → dedupe.
- **Region still blank after gold** → the city→region case expression missed Logan or Provo;
  check spelling and that the expression runs on the *trimmed* city.

## If you're short on time
Drop the optional PK/comments (Step 7.3) and the standalone silver materialization — a single
Designer flow (bronze source → transforms → gold output) is enough to tell the whole story. Do
**not** skip the lineage view; it's the payoff shot.

## The bridge to the AI/BI half
Close with: *"The `dim_facility` you just built is the same kind of governed table the dashboards
and Genie read. Now let's go use tables like it."* Then move to `attendee_workbook.md`.
