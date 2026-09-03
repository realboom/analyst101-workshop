# Instructor Guide — Analyst 101 Workshop

**For:** workshop facilitators (lead + floating support).
**Audience:** a mixed group of analysts/business users — some SQL-comfortable, some newer to
Databricks, some coming from Tableau. Meet each where they are.
**Style:** Hands-on, light on theory. Talk for a few minutes, then everyone clicks. Build in breaks.

This guide covers the **whole workshop** and pairs with the **Attendee Workbook** (Part 0 = the
Foundations + ETL lab; Parts 1–4 = the AI/BI half). The **Foundations + ETL** facilitator playbook is
the first section below; the **AI/BI** segment playbook follows it. Bridge from ETL into the AI/BI
half with: *"the `dim_facility` you just built is the same kind of table the dashboards read."* Live
asset links and IDs are in `workshop_assets.md`. All data is synthetic, no PHI.

---

## How to frame the whole workshop (read this first)

The single most important framing:

> **This is Analyst 101 — from a raw file to a governed insight.** The story is that the whole path
> lives in one governed platform: land a file, refine it in layers (bronze→silver→gold), and turn
> the result into dashboards and plain-language Q&A with Genie. For teams coming from Tableau, be
> clear this is not a one-to-one replacement and we aren't aspiring to win a feature-by-feature
> bake-off — we're showing the art of the possible and being honest about trade-offs.

Three things to keep saying:
1. **"Your data is already here."** Most of their analytics data is landing in Databricks. AI/BI
   runs directly on it with no extract, no separate server, and the compute is the same compute
   they already pay for. Moving a dashboard here is low friction, not a big new cost.
2. **"Consumption is changing."** The differentiator is not prettier charts. It is Genie (ask in
   plain language), one governed definition of a metric, and AI-assisted authoring.
3. **"Here is the honest trade-off."** Be upfront about where Tableau is still ahead (see the
   trade-offs slide and segment). Credibility with this group comes from naming the gaps, not
   hiding them. Frame the day as a learning session, and meet skepticism halfway by being candid.

**Reading the room:** skeptics will probe SQL dialect, governance, and "why would I bother."
Lean into "the SQL is always one click away" and "the metric is defined once, by you." Eager
adopters will want to push into advanced features; have pointers ready but do not let the room
rabbit-hole.

---

## Pre-flight checklist (do the day before)

- [ ] Dataset generated into `{{CATALOG}}.{{SCHEMA}}` in the workshop workspace
      (run `data_generation/generate_workshop_data.py`; see `../TEMPLATE.md`).
- [ ] All 3 attendees can log into the workspace and have SELECT on `{{CATALOG}}.{{SCHEMA}}`.
- [ ] A SQL warehouse (serverless or pro) is running, or set to auto-start.
- [ ] Dashboard imported (`dashboard/{{SCHEMA}}.lvdash.json`) and every widget renders.
- [ ] Confirm you can create a Genie Agent (**Genie Agents → New** → pick tables) in this workspace
      (so the live Day-1 flow works), and have the paste-in instructions block handy.
- [ ] (Backup) Pre-built standalone Genie Agent created and answers the {{PROCEDURE_EXAMPLE}} question,
      in case creating one live hiccups.
- [ ] Slide deck open and ready to present.
- [ ] Decide: do attendees each clone the starter dashboard, or build their own from scratch?
      (Recommended: build their own on Day 1 so they learn the authoring flow; reference the
      starter when they get stuck.)
- [ ] Dry-run option: rehearse the full flow in a staging schema before the workshop
      workspace is set up (see `workshop_assets.md`).

---

> **On the day/time structure below:** the "Day 1 / Day 2" split and clock times are the original
> AI/BI-only cadence and are illustrative. For the Analyst 101 session, **follow `agenda.md`** — it
> front-loads the Foundations + ETL lab, then draws on the AI/BI segments below. Treat what follows
> as a segment **playbook** to pull from, sized to whatever block your agenda gives the AI/BI half.

# Foundations + ETL lab (instructor playbook)

**The lab:** Attendee Workbook **Part 0**. Attendees create their own schema + a volume, upload their
profile's `facilities_raw.<profile>.csv`, and build a no-code **bronze → silver → gold** pipeline in
**Lakeflow Designer** that lands a clean `dim_facility`. This is the Analyst 101 foundations
front-half; the AI/BI half follows on the pre-built shared star schema.

**Time budget:** ~45–55 min. Concepts 5 · Volume + upload 8 · Bronze 7 · Silver 15 · Gold 10 ·
Verify/lineage 8.

## The one thing to land
Data-quality work is real work, and Databricks lets an analyst do it **visually, governed, and
repeatable** — not in a throwaway spreadsheet. Every messy thing in the file maps to one Designer
operator. By the end they have a lineage graph and a table they could schedule nightly.

## Cadence: "watch me, then you do it"
Designer is new to most attendees. Demo Workbook Part 0 Steps 3–4 (start a build, add the bronze
source) live on the projector once, then let them do it. Do **Silver together, operator by operator**,
pausing on each live preview so they see the change. **Gold** they can mostly drive themselves; float
and help. Everyone then runs **Step 6** (table + column comments and a primary key) — don't skip it:
it's the metadata that makes their `dim_facility` usable by Genie in Part 4, and it's the hands-on
version of the Databricks Day slide-8 lesson (*the setup drives the answer*).

## What each messy element teaches (and the operator that fixes it)
| In the raw file | Layer | Designer operator |
|---|---|---|
| Leading/trailing spaces on names | Silver | Trim / clean |
| `State` as full name / code / mixed case ("Utah" / "UT " / "ut") | Silver | Upper + map to 2-letter (standard US-state lookup) |
| `Type` in mixed casing ("pediatric clinic" / "PEDIATRIC CLINIC") | Silver | Title-case |
| Trailing blank line | Silver | Filter `Facility ID` not null |
| One duplicated facility row | Silver | Deduplicate on `facility_id` |
| Blank `Region` on two facilities (each shares a City with a sibling) | Gold | Fill from same-city sibling (window by `City`) |
| `Facility ID` → `facility_id` etc. | Gold | Rename to snake_case |

**Order matters — call it out:** standardize *before* you dedupe, or the duplicated rows won't match.
This is a genuine ETL lesson, not a Databricks quirk. **Expected end state:** exactly **12 rows**,
clean 2-letter states, proper-cased types, no null regions. (Validated per profile:
`python etl_lab/build_raw_csv.py --all --check`.)

## Step 6 — "make it Genie-ready" (the slide-8 metadata lesson)
This is where the ETL lab connects to the Databricks Day *Maturing Genie* story (slides 6–9). Land the
message from **slide 8** — *"start with the data, not the prompt; the setup drives the answer"*:
- **Table + column comments and a declared key are the *context* Genie reads.** A well-annotated,
  well-modeled table gets good answers; a raw, uncommented one gets guesses.
- Their freshly-built `dim_facility` starts with **no comments and no key** (Designer doesn't add them),
  so it's the perfect "before." Running Step 6's SQL is them *tailoring the table for Genie*.
- Have them **reopen the table in Catalog and compare to a shared table** (e.g. `dim_provider`) — same
  treatment: every column described, PK defined. Point out the shared tables ship this way, which is
  why Genie answers well on them out of the box.
- Tie forward: in **Part 4** they point Genie at *this* table; the annotation is why facility/region
  questions resolve reliably. Also mention the other slide-8/9 levers we go deep on at Databricks Day —
  **tight scope** (≤5 well-modeled tables), **explicit many-to-one joins**, and **SQL-based
  instructions/example queries** over free text.

## Prerequisites BEFORE the session (one-time, group-level)
- **Serverless compute** available (Designer runs on serverless).
- The workshop group has, on `{{CATALOG}}`: `USE CATALOG` + **`CREATE SCHEMA`** (so each attendee can
  create their own schema in the lab), and `USE SCHEMA` + `SELECT` on `{{CATALOG}}.{{SCHEMA}}`.
  Attendees **create their own** `{{CATALOG}}.analyst101_<user>` schema as Step 1 — they own it, so
  `CREATE VOLUME` / `CREATE TABLE` come automatically. No per-attendee provisioning by the instructor.
- Attendees can reach **Lakeflow / Designer** (Data Engineering entitlement).
- The profile's `etl_lab/facilities_raw.<profile>.csv` shared with attendees (Slack/email/repo link),
  or pre-staged in a shared volume (the data generator has an optional `stage_raw_csv` cell).

## Common gotchas
- **"I can't create a schema"** → the group is missing `CREATE SCHEMA` on `{{CATALOG}}`. Fix:
  ``GRANT CREATE SCHEMA ON CATALOG {{CATALOG}} TO `analyst101_attendees`;`` then they re-run
  `CREATE SCHEMA {{CATALOG}}.analyst101_<their-name>`.
- **"I don't see Create Volume / can't create a table"** → they're pointed at a schema they don't own
  (e.g. the shared one). Confirm they're in **their own** `analyst101_<user>` schema.
- **"Designer won't start / no compute"** → serverless not enabled or not selected.
- **Source parsed as one column** → header/delimiter detection; re-open the source pane and confirm
  comma-delimited with header row.
- **Dedup left 13 rows** → they deduped *before* standardizing; reorder: clean → standardize → dedupe.
- **Region still blank after gold** → the same-city fill ran on the *untrimmed* City; trim City first,
  then partition by City.

## If you're short on time
Drop any standalone silver materialization — a single Designer flow (bronze source → transforms → gold
output) tells the whole story. Do **not** skip the **lineage view** (the payoff shot) or **Step 6**
(comments + key) — Step 6 is the Genie-context lesson and Part 4 points Genie at this table. If truly
rushed, keep the table comment + PK + a couple of column comments rather than all six.

## The bridge to the AI/BI half
Close with: *"The `dim_facility` you just built is the same kind of governed table the dashboards and
Genie read. Now let's go use tables like it."* Then move into Part 1 of the workbook.

---

# DAY 1 - What's possible in AI/BI (~3h50, 12:00-3:50 CT)

## Segment 0 - Orientation slides (12:00-12:20)

**Goal:** Set expectations, give just enough Databricks/UC/AI/BI grounding, and land the Tableau
trade-off framing before anyone touches a keyboard.

**Run the slide deck** (see the orientation deck). Keep it to ~20 minutes. Slide-by-slide notes:

| Slide | Say this | Point out |
|---|---|---|
| Title | "Two days, hands-on. Today is what's possible, tomorrow you build your own." | Set the hands-on tone immediately. |
| What to expect | "Light on theory. We talk for a few minutes, then you click." | Tell them to keep the workspace open and follow along. |
| Databricks + Unity Catalog in 2 min | "Your data lands once in the lakehouse; Unity Catalog governs who sees what. AI/BI and Genie read straight from it." | The "data is already here" point. No extracts, no separate BI server. |
| What is an AI/BI Dashboard (+ Genie) | "A dashboard is datasets plus visuals on a canvas. Genie lets anyone ask questions in plain English on the same governed data." | These are the two things they will build today. |
| **Not 1:1 with Tableau (trade-offs)** | Use the script below. This is the most important slide. | Name what they gain and what they give up. Be honest. |
| How this maps to your Tableau workflow | Walk the parity table (workbook to dashboard, published data source to metric view, Ask Data to Genie). | Anchor every new term to something they already know. |
| Let's build | "Two ways to build: ask Genie, or author manually. You'll do both." | Transition to hands-on. |

**Trade-offs slide talk track (memorize the spirit of this):**
> "Quick reality check so we're all honest with each other. AI/BI dashboards are not a one-to-one
> replacement for Tableau, and we're not going to pretend they are. There are things Tableau still
> does better: very precise pixel-level formatting, some advanced chart types, and the deep muscle
> memory your team has built. What you gain is different: you ask questions in plain language with
> Genie, your metric definitions live in one governed place so everyone's numbers match, authoring
> is AI-assisted, and because your data and compute already live in Databricks there's no extract
> and no big new cost to move a dashboard here. So the question for the two days isn't 'is this
> Tableau,' it's 'where does this way of working make your life easier, and where would you keep
> Tableau.'"

**Watch for:** if the skeptic challenges early ("why move at all"), acknowledge it and say "that's
exactly what these two days are for, let's see where it helps and where it doesn't." Do not get
defensive.

---

## Segment 1 - The dataset as an analytics engine (12:20-1:05)

**Goal:** Establish credibility fast. These are senior analysts who do complex work in Tableau, so do
NOT linger on "drop a bar chart." Lead with the point that a dataset is full Databricks SQL, so their
table calcs / LOD / rank work are just window functions here, defined once and reused. Build a ranked,
binned provider scorecard and a period-over-period trend.

**Say:** "A dataset here is just SQL, so everything you do with table calcs and LOD in Tableau, you do
with window functions, and it lives in one governed place instead of per-worksheet. Let's go straight
at the real analysis."

**Do (Attendee Workbook, Part 1):**
1. **Dashboards** > **Create dashboard**, name it.
2. `Provider performance` dataset: the percentile-rank + `NTILE(4)` quartile query (Workbook Part 1,
   Step 2). Add a **Table**, then **conditional formatting** to color the quartile / rate. This is a
   ranked, risk-binned scorecard with no table-calc plumbing.
3. `Outcome trend` dataset: the `LAG` period-over-period + windowed rolling-average query. Add a
   **Combo** chart (bars = encounters, line = `rolling_3mo` on a second axis).
4. **Calculated fields (no code):** on a small row-level dataset from `fact_encounters`, add a
   calculated dimension (`age_band` via CASE) plus calculated measures for average charges and average
   paid, then chart cost by age band. Their Tableau calculated field, in the dataset. (Dropped the old
   paid-to-charge ratio — on the synthetic data it was flat and unconvincing.)

**Point out:**
- `PERCENT_RANK` / `NTILE` = their rank table calcs; `LAG` and the windowed `AVG` = running/difference
  and trailing-average table calcs; the calculated measure/dimension = their calculated field. Reused
  by every widget, governed, version-controllable.
- The escape hatch: anything expressible in SQL (including `QUALIFY`, percentiles, CTEs) is first-class.
- No extract, no refresh schedule. Live on the lakehouse.

**Checkpoint:** everyone has the ranked scorecard table + the combo trend. A facilitator floats. Do not move on
until all three are caught up.

### Break (1:05-1:20)

---

## Segment 2 - Advanced visuals, parameters, and benchmarks (1:20-2:10)

**Goal:** Push into the power-user surface: a parameter that re-thresholds the analysis live, a
peer-group benchmark (window over a grouped aggregate), a heatmap, a choropleth map, a pivot table, and
the interactivity (cross-filter, drill). This is where the Tableau-heavy analyst decides this is serious.

**Do (Workbook Part 2):**
1. **Parameter:** add a `min_encounters` parameter (default 200) and wire it into the
   `Provider performance` dataset HAVING clause (`HAVING COUNT(*) >= :min_encounters`). Change the value
   and watch the scorecard re-threshold live. Call out this is their Tableau parameter, driving SQL.
2. **Benchmark vs peer group:** `Facility vs region` dataset (the `AVG(...) OVER (PARTITION BY region)`
   pattern), shown as a table with diverging conditional formatting on `vs_region_avg_pts`.
3. **Heatmap:** `Category x region` complication rate.
4. **Map:** choropleth on `state` colored by readmission rate.
5. **Pivot table:** clinical_category x encounter_type.
6. **Forecasting + AI functions:** `ai_forecast` to project the next six months of volume (verified to
   run on this data); name-drop `ai_query` / `ai_classify` / `ai_extract` as same-SQL built-ins.
7. **Interactivity:** region filter + date-range filter, cross-filtering on click, and a
   region > facility > provider drill hierarchy.
8. **Multipage reporting:** split into pages (Overview / Provider performance / Geography) using the
   page tabs, with shared filters. Mention themes exist but we are not focused on branding (the sponsor
   deferred it).

**Point out:**
- This is the full capability surface: rich visuals, calculated fields, parameters, cross-filter,
  drill, forecasting, multipage. Parameters + window functions + `QUALIFY` cover the large majority of
  what they reach for table calcs and LOD to do in Tableau.
- Be honest where Tableau still leads: very fine-grained reference lines/bands, a few niche chart types,
  some LOD nuance. The counter: SQL is always available, so they are rarely boxed in.

**Watch for:** the eager analyst will want to stress-test it. Let them throw a hard ask at a dataset and
solve it in SQL live. The skeptic cares about governance: emphasize definitions live in the dataset /
metric view, not scattered across workbooks.

### Break (2:10-2:25)

---

## Segment 3 - Build with AI: assisted authoring + the semantic layer (2:25-3:05)

**Goal:** Show the "build with Genie/AI" path for authoring, and introduce metric views as the
governed definition layer (the Tableau published-data-source parity story).

**Do (Workbook Part 3):**
1. Open the dashboard **Assistant** and type a plain-English ask, e.g. "Show average length of stay
   by specialty as a bar chart." Accept and tweak. Then show editing the underlying SQL for
   precision.
2. Introduce **metric views**: "This is your published data source. Measures and dimensions defined
   once, governed, reused in dashboards and Genie." Show the concept (a readmission-rate measure
   defined once).
3. **Publish** the dashboard (top-right **Publish**) to close out the build — it's now shareable and
   everyone sees the same governed numbers.

**Point out:**
- One definition of "readmission rate," used identically everywhere. No more three analysts with
  three slightly different numbers. This is the governance answer the skeptic is probing for.
- AI-assisted authoring is a drafting accelerator, not a replacement for their judgment.

---

## Segment 4 - Stand up a Genie Agent (3:05-3:40)

> **Naming note:** "Genie spaces" are now **Genie Agents** in the UI. Creating one *from a dashboard*
> is no longer a reliable button — create the agent from the **Genie Agents** sidebar on the same
> tables. The published dashboard's **Ask Genie** box is a quick embedded ask, not the full agent.

**Goal:** Each analyst creates a **Genie Agent** on the same data they just built the dashboard on,
pastes in a short instructions block, and asks a few questions. This is the centerpiece: it shows
how AI/BI and Genie connect, and how little it takes to get a good agent when the data is well
documented. Best segment for the skeptic.

**Say:** "You just built a dashboard. Watch how fast we can stand up a Genie Agent anyone can ask
questions of. The reason it works so well, with almost no setup, is that this data is fully
documented: every column has a description and the table relationships are defined, so Genie already
knows how to join things. We just add a few instructions on top."

**Do (Workbook Part 4) - everyone on their own:**
1. Left sidebar → **Genie Agents** → **New** → select shared `fact_encounters`, `dim_provider`,
   `dim_diagnosis`, `dim_procedure`, and the shared **`dim_facility`** → **Create**. The Genie Agent is
   created — instructions and trusted assets go in its **Configuration** (**Configure**, top-right).
   *(If an attendee built their own `analyst101_<user>.dim_facility` in Part 0,
   have them add **that** one instead of the shared `dim_facility` — it has the same `facility_id`s, so
   it joins to `fact_encounters` cleanly, and it closes the loop from their ETL build. Their own table
   has no declared FK, so that join relies on the instruction hint in the block, not auto-FK metadata.)*
2. Click **Configure** (top-right) → in the **Configuration** (the agent's **Instructions** area), **paste the prepared instructions block**
   (in `genie/genie_space_config.md`, also pre-shared in the Workbook). Save.
3. Let the **attendees drive**. Have them ask a few:
   - "How many encounters were there in 2024 by region?"
   - "Which providers have the highest 30-day readmission rate, with at least 200 encounters?"
   - "What is the average length of stay for a {{PROCEDURE_EXAMPLE}}?"
4. On each answer, click **Show generated code** so they see the Databricks SQL.

**Point out (skeptic-focused):**
- The quality comes from the **column comments and foreign keys** (already in the data) plus the short
  instructions block, not heavy configuration. Open a table in Catalog and show the comments + the
  PK/FK if they are curious.
- "Genie writes Databricks SQL, so it's a fast way to see the right dialect and functions when you
  translate what you already write." (The skeptic's stated use.)
- Trust and governance: the end-user feedback options (**Yes / Fix it / Request review**), the
  **Analysis** view, and that Genie only sees tables you grant.

### Optional: the before/after "tailoring" demo (instructor-driven)
Ask the same questions on a **bare agent** (tables only — no synonyms / SQL expressions / example
query / instructions) and on the **tuned agent**, and compare. Keep it instructor-driven, not hands-on.

**Be honest about this schema first.** It's clean, small, and fully commented, so the bare agent is
*already good* — that itself is the lesson ("the setup drives the answer": good names + comments +
keys carry Genie). Don't stage this as "watch the bare agent fail on basic questions" — it won't, and
a smart analyst audience will see through it. The following are **verified** on this dataset (asked on
both agents); use these, not a strawman:

| Ask this | Bare agent (verified) | Tuned agent (verified) | What it shows |
|---|---|---|---|
| **"Which facilities are the most expensive?"** | *hedges* — picks `SUM(total_charges)`, then asks "average per encounter instead?" (ambiguous: total vs average, charges vs paid) | **decisive** — `AVG(total_charges)` per encounter, rounded, ranked, clean $ answer | tuning **resolves ambiguity** → a confident, consistent answer. The strongest live contrast. |
| **Same metric asked a few ways** ("bounce-back rate by facility", "highest readmission doctors") | understands the terms, but the **shape varies** — raw fractions (`0.1255`), `SUM` vs `AVG`, sometimes a single `RANK()=1` row | consistent governed shape every time — `AVG(...)*100`, one decimal, `HAVING COUNT(*)>=200`, clean ranked list | **consistency** across phrasings — deck **slide 6** ("same question, different SQL on different days") |

**What synonyms do — and don't — show here (say so if asked):** synonyms for well-named columns
("LOS" → `length_of_stay_days`, "bounce-back" → `readmitted_30d`) **don't change the answer** — the
bare agent maps those from the column name + comment. What *does* change (and what the workbook's
synonym demo hangs on): asked cold, Genie **hedges the interpretation** — *"I interpreted bounce-back
rate as the 30-day readmission rate…"*; pinning the synonym removes that guess. So frame it as
**governance, not capability** — a pinned mapping no one downstream has to trust an inference on — not
"watch it fail." On a real, cryptic schema (`PROV_RNDR_NPI`, `DSCHG_DISP_CD`) synonyms would earn
their keep on the **answer** too; here they earn it on the **caveat**. And the ≥200-encounter floor is
a **no-op** on this data (every provider has 271+ encounters), so it never changes a ranking. That
honesty *is* the credibility.

**A nice tell:** the tuned agent's SQL visibly carries the **example query's house style** —
`ROUND(...*100,1)` and `HAVING COUNT(*)>=200` show up even where not strictly needed — and it joined to
the attendee's *own* `analyst101_<user>.dim_facility` (loop-closing working). That's the example query
and the Part-0 table doing their jobs.

**The real "wow" is Day 2, not here:** PCP continuity needs business logic Genie can't infer
(standard-visits-only + attending-vs-assigned-PCP). A naive agent can't get it right; the trusted
metric view / function does. Run that before/after in the Day-2 spotlight.

**Run it:** ask on the bare agent and the tuned agent side by side (a pre-built bare agent, tables
only, is fine). **Genie is non-deterministic** — the ambiguity hedge won't fire every single time — so
**pre-run the exact questions the morning of**. (Also: a Genie **SQL expression** never appears by name
in the generated SQL — it's expanded inline — so you can't attribute output to it by reading the SQL;
the metric view / SQL functions on Day 2 *are* referenced by name, which is the observability contrast.)

**Watch for:**
- If creating the agent hiccups for someone, fall back to the **pre-built standalone Genie Agent**
  (`workshop_assets.md`) so the segment keeps moving.
- If Genie gets one wrong, that's a feature, not a failure. Use **Fix it** to show the human-in-the-loop
  loop. Do not hide it.

---

## Segment 5 - Wrap and Day-2 setup (3:40-3:50)

- Recap the two ways to build (manual + AI/Genie) and the metric-view governance point.
- **Confirm each analyst's Day-2 scenario:** a question they want answered or a report/dashboard they
  want to recreate. Capture it so anything needed can be pre-staged tonight.
- Tee up the idea: if they bring an existing Tableau dashboard, Day 2 can be "let's rebuild one
  of yours and see what the experience is like."

---

# DAY 2 - Advanced features + build-your-own (~1h50, 12:00-1:50 CT)

Day 2 mirrors the **Databricks Day advanced half** (the "confidence stack": trusted SQL functions →
metric views → trusted assets in Genie), then closes with a free build and a take-home capstone
attendees run on their own data. All the advanced
assets are pre-deployed on the shared schema (`pcp_continuity_metrics` + the 3 functions); see
`advanced_module/README.md` for the deploy + the demo talk track that maps to the deck.

## Segment 0 - Recap and plan (12:00-12:10)
- 60-second refresher. Lay out: advanced module (~40 min), then build + share-outs.
- Frame the day: Day 1 was *fast* answers; Day 2 is *trustworthy* answers — governed metrics.

## Segment 1 - Advanced features: governed metrics & trusted assets (12:10-12:55)
Walk the **Workbook Day-2 Parts 5–8** on the PCP-continuity use case. This is the hands-on version of
your Databricks Day demo:
- **Part 5 — SQL functions:** call `pcp_continuity_by_provider()` by name — the provider grain the
  metric view can't produce; deterministic, `EXECUTE`-granted, logic hidden (PHI-safe). *(We feature
  just this one function now — the overall/facility/region ratio is covered by the metric view in
  Part 6.)* *(Deck slides 12–14.)*
- **Part 6 — metric views:** query `pcp_continuity_metrics` with `MEASURE()`; re-slice by
  `Facility` → `Region` → `Encounter Month`. Land the **query-time grouping** point — continuity is a
  *ratio* (non-additive), so the view keeps it correct at every grain where a copy-pasted calc field
  wouldn't. *(Slides 15–19.)*
- **Part 7 — trusted assets + the benchmark:** the money demo, **verified**. On the NAIVE agent, ask
  *"overall PCP continuity rate?"* → **76.3%** (Genie infers the standard-visits restriction from the
  phrasing) vs *"what share of visits are with the patient's PCP?"* → **65.5%** (counts all visit
  types). Same
  question, 11-point swing by phrasing — best-effort is *inconsistent*. On the GOVERNED agent (metric
  view + function in scope) both phrasings anchor to **76.3%**. **Be accurate on the mechanism:** per
  Databricks docs, Genie is **nondeterministic even with trusted assets** — it decides whether to call
  the asset (Trusted badge when it does) or hand-write SQL from the governed definition as context. The
  real determinism is the **metric view / function called directly** (SQL, dashboards) — one governed
  definition, same number every time; in Genie they *anchor* answers rather than *guarantee* a call.
  Don't promise "it always calls the function by name." *(Slides 6, 12, 16, 20 — note the deck's
  "deterministic" framing is aspirational; the governed-definition-as-anchor is the honest version.)*
  **Config that works (tested) — the escalation ladder maps to deck slide 13:**
  - *Metric view:* register it **and** add a routing instruction ("for PCP continuity use
    `pcp_continuity_metrics`"). Registering alone left Genie hand-writing SQL; with the instruction it
    called `MEASURE()` by name on all phrasings → 76.3%.
  - *Function:* register + instruction was **not** enough — Genie kept preferring the metric view (even
    hallucinating a nonexistent `Provider` dim rather than call the function). What worked: an
    **example query** whose SQL calls the function. Tested — pairing *"which providers have the lowest
    PCP continuity?"* to a `pcp_continuity_by_provider()` example query made Genie call the function.
  - So the ladder is: **register → instruct → example query**, escalating until Genie uses the asset.
    Functions generally need the example query; the metric view often just needs the instruction.
  - **Monitoring + Benchmarks tabs (2 min, show live):** open the agent's **Benchmarks** tab and run
    the continuity question as a benchmark row to *quantify* the lift (naive **65.5%** → governed
    **76.3%**), not just eyeball one answer; open **Monitoring** to show the real question log + 👍/👎 /
    *Fix it* feedback that becomes the curation backlog. Framing: **Monitoring = what to fix, trusted
    assets = the fix, Benchmarks = proof it holds.**
- **Part 8 — author your own (extra, if time):** hands-on authoring reps on the *synthetic* data — a
  metric-view measure (AI-assisted or YAML) and a SQL function, built in their own schema. It's the
  syntax/pattern for standing these up on their real data later, not a "bring your own data" step.

**Coaching cues:** query-focused/skeptics love Parts 5–7 (governed, auditable, referenced by name);
Tableau-heavy attendees — anchor the metric view to "published data source, but one definition for
*every* tool." Keep authoring (Part 8) light for a mixed room; it's a take-home pattern, not a stall point.

> **Benchmark is verified** (tested via the Genie API): governed number = **76.3%**; a bare agent
> gives 76.3% for "continuity rate" but **65.5%** for "share of visits with the patient's PCP" (counts
> all visit types — the standard-visits rule isn't in the data, only in the governed assets) — the
> phrasing-variance contrast is real. **Still verify the inferred
> UI labels live:** the **trusted assets** location in the **Configuration**, the **"Trusted" badge**,
> **Catalog Explorer → Create → Metric view** AI-assisted authoring, and the **Monitoring** /
> **Benchmarks** tab labels + flow — fix any that drift.

### Break (12:55-1:05)

## Segment 2 - Free build + capstone planning + share-outs (1:05-1:45)
Two tracks — let each analyst pick: **(a) cement the skills** with a last free-build on the synthetic
`{{CATALOG}}.{{SCHEMA}}` (a scorecard, a scatter, a Genie-first exploration, a governed metric from
Segment 1), or **(b) plan their take-home** — the Attendee Workbook **Capstone** is now a *leave-behind*
they run on their **own** data, so use this time to help them map their real fact/dimension tables,
pick the first dashboard or Genie Agent to build, and name the metric worth governing first.
Facilitators float. Then each shares 3–5 minutes: what they built on the synthetic data **and/or what
they'll build back home**.
- Handle advanced asks live: drill hierarchies, calculated measures, Genie follow-ups, saving a
  Genie answer into a dashboard, and the publish/share/permissions story versus Tableau Server.

## Segment 3 - Wrap and next steps (1:45-1:50)
- Map to reality: "Everything you did sits on synthetic data, but the exact same flow works on your
  real tables once they're in Databricks." Note Unity Catalog governance and that metric
  views keep definitions consistent.
- Be honest about trade-offs one more time, and capture the team's read (this is the sponsor's assessment
  to advise other teams).
- Next steps: who follows up, what to pilot on real data, any access or enablement gaps.

---

## Migrating an existing Tableau dashboard (if the sponsor or attendees ask)

Be accurate and do not over-promise a product button.

- **There is no GA, self-serve "upload your Tableau workbook, get an AI/BI dashboard" feature today.** Don't imply one exists.
- **The reliable path, and what we do on Day 2, is an assistant-assisted rebuild.** Point the AI/BI Assistant at a good wide dataset and it gets you most of the way fast for a standard dashboard. This is the "rebuild one of their dashboards" idea, and it does not depend on any experimental tooling.
- **Internal migration tooling exists, but it is FE-run, not customer DIY:**
  - **TeleportBI** converts Tableau workbook (.twb) files to AI/BI dashboard JSON (.lvdash.json), with a validation framework. Experimental (engineering sandbox), Tableau-first.
  - **Genie Code migration agents:** emerging in-editor agents for Power BI and Tableau migration.
  - The most mature tool today is **Power BI only** (DAX to SQL, semantic model to metric views plus a Lakeview dashboard), so it does not cover Tableau yet.
- **How to frame it to the sponsor:** "Databricks has migration tooling, and we can convert your Tableau content as a follow-on." Then loop in FE to run TeleportBI or the Genie Code agents with a Databricks person driving. Keep it a follow-on engagement, not a live workshop deliverable.
- Internal references: TeleportBI (Confluence `/spaces/UN/pages/5353505269`), Power BI tool (`/spaces/FE/pages/6178669940`).

---

## Appendix - Anticipated questions and answers

- **"Can this fully replace Tableau?"** "Not one-to-one, and that's not the goal. It replaces a lot of
  day-to-day reporting and adds natural-language access. Some advanced Tableau viz and formatting you'd
  keep. The win is that it runs on data you already have in Databricks, governed once."
- **"How does Tableau connect to Databricks today?"** Via JDBC, the same as any external BI tool. With
  a locked-down workspace there's networking to punch through. Part of their data already flows from
  Databricks to Tableau, so the connection pattern exists. AI/BI skips that hop entirely.
- **"Is this a big new cost?"** No large net-new cost: the data is already in Databricks and AI/BI uses
  the same compute. (Relevant for cost-conscious teams.)
- **"What about pixel-perfect formatting / specific chart types?"** Tableau is still ahead on some of
  this. Name it honestly; show what AI/BI does well and where the trade-off lands.
- **"Does Genie make things up?"** It generates SQL you can inspect and correct; it only sees granted
  tables; feedback (Yes / Fix it / Request review) keeps a human in the loop.
