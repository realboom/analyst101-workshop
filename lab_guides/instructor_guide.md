# Instructor Guide - {{CLIENT_NAME}} Analyst 101 Workshop (AI/BI half)

**For:** workshop facilitators (lead + floating support).
**Audience:** a mixed group of analysts/business users — some SQL-comfortable, some newer to
Databricks, some coming from Tableau. Meet each where they are.
**Style:** Hands-on, light on theory. Talk for a few minutes, then everyone clicks. Build in breaks.

This is the **AI/BI half**. It follows the **Foundations + ETL lab** (`etl_lab/etl_lab_guide.md`
and `etl_lab/etl_instructor_notes.md`), where attendees create a volume, upload a file, and build
a `dim_facility` table in Lakeflow Designer. Bridge into this half with: *"the table you just built
is the same kind the dashboards read."* This guide pairs with the **Attendee Workbook**. Live asset
links and IDs are in `workshop_assets.md`. All data is synthetic, no PHI.

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

- [ ] Dataset generated into `{{CATALOG}}.{{SCHEMA}}` in the {{CLIENT_NAME}} workspace
      (run `data_generation/generate_workshop_data.py`; see `../TEMPLATE.md`).
- [ ] All 3 attendees can log into the workspace and have SELECT on `{{CATALOG}}.{{SCHEMA}}`.
- [ ] A SQL warehouse (serverless or pro) is running, or set to auto-start.
- [ ] Dashboard imported (`dashboard/{{SCHEMA}}.lvdash.json`) and every widget renders.
- [ ] Confirm you can publish a dashboard and create a Genie space from it in this workspace
      (so the live Day-1 flow works), and have the paste-in instructions block handy.
- [ ] (Backup) Pre-built standalone Genie space created and answers the knee-replacement question,
      in case the live publish step hiccups.
- [ ] Slide deck open and ready to present.
- [ ] Decide: do attendees each clone the starter dashboard, or build their own from scratch?
      (Recommended: build their own on Day 1 so they learn the authoring flow; reference the
      starter when they get stuck.)
- [ ] Dry-run option: rehearse the full flow in a staging schema before the {{CLIENT_NAME}}
      workspace is set up (see `workshop_assets.md`).

---

> **On the day/time structure below:** the "Day 1 / Day 2" split and clock times are the original
> AI/BI-only cadence and are illustrative. For the Analyst 101 session, **follow `agenda.md`** — it
> front-loads the Foundations + ETL lab, then draws on the AI/BI segments below. Treat what follows
> as a segment **playbook** to pull from, sized to whatever block your agenda gives the AI/BI half.

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
4. **Calculated measure + dimension (no code):** add a calculated measure (paid-to-charge ratio) and a
   calculated dimension (age band via CASE). Their Tableau calculated field, in the dataset.

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

**Point out:**
- One definition of "readmission rate," used identically everywhere. No more three analysts with
  three slightly different numbers. This is the governance answer the skeptic is probing for.
- AI-assisted authoring is a drafting accelerator, not a replacement for their judgment.

---

## Segment 4 - Publish your dashboard and stand up its Genie space (3:05-3:40)

**Goal:** Each analyst publishes the dashboard they just built, creates a Genie space directly from
it, pastes in a short instructions block, and asks a few questions. This is the centerpiece: it shows
how AI/BI and Genie connect, and how little it takes to get a good Genie space when the data is well
documented. Best segment for the skeptic.

**Say:** "You just built a dashboard. Watch how fast we can turn that into a Genie space anyone can
ask questions of. The reason it works so well, with almost no setup, is that this data is fully
documented: every column has a description and the table relationships are defined, so Genie already
knows how to join things. We just add a few instructions on top."

**Do (Workbook Part 4) - everyone on their own dashboard:**
1. **Publish** your dashboard (top-right **Publish**).
2. From the dashboard, **create a Genie space from it** (the Genie / "Create Genie space" control on
   the dashboard). This generates a space using your dashboard's data.
3. Open the new Genie space, go to **Instructions**, and **paste the prepared instructions block**
   (in `genie/genie_space_config.md`, also pre-shared in the Workbook). Save.
4. Let the **attendees drive**. Have them ask a few:
   - "How many encounters were there in 2024 by region?"
   - "Which providers have the highest 30-day readmission rate, with at least 200 encounters?"
   - "What is the average length of stay for a knee replacement?"
5. On each answer, click **Show generated code** so they see the Databricks SQL.

**Point out (skeptic-focused):**
- The quality comes from the **column comments and foreign keys** (already in the data) plus the short
  instructions block, not heavy configuration. Open a table in Catalog and show the comments + the
  PK/FK if they are curious.
- "Genie writes Databricks SQL, so it's a fast way to see the right dialect and functions when you
  translate what you already write." (The skeptic's stated use.)
- Trust and governance: the end-user feedback options (**Yes / Fix it / Request review**), the
  **Analysis** view, and that Genie only sees tables you grant.

**Watch for:**
- If the publish-to-Genie step misbehaves for someone, fall back to the **pre-built standalone Genie
  space** (`workshop_assets.md`) so the segment keeps moving.
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

# DAY 2 - Build with your own scenario (~1h50, 12:00-1:50 CT)

## Segment 0 - Recap and plan (12:00-12:10)
- 60-second refresher. Lay out: ~50 minutes build, then share-outs.
- Restate each analyst's scenario so expectations are set.

## Segment 1 - Hands-on build (12:10-1:00)
Each analyst builds on `{{CATALOG}}.{{SCHEMA}}` (or rebuilds one of their own Tableau
dashboards). Facilitators float. Starter scenarios are in the Attendee Workbook, Day 2.

**Coaching cues by person:**
- **Query-focused / skeptic:** push on metric views and the SQL behind visuals; let them drive Genie
  and always reveal the SQL.
- **Tableau-heavy / eager:** map each step to its Tableau equivalent; show cross-filtering and drill
  as the "free" wins; if there's appetite, mention dashboard/widget JSON customization (a newer
  AI/BI capability) as a power-user feature.

### Break (1:00-1:10)

## Segment 2 - Share-outs and advanced asks (1:10-1:40)
- Each analyst shares for 3-5 minutes: what they built, what surprised them.
- Handle advanced asks live: drill hierarchies, calculated measures, Genie follow-ups, saving a
  Genie answer into a dashboard, and the publish/share/permissions story versus Tableau Server.

## Segment 3 - Wrap and next steps (1:40-1:50)
- Map to reality: "Everything you did sits on synthetic data, but the exact same flow works on your
  real {{CLIENT_NAME}} tables once they're in Databricks." Note Unity Catalog governance and that metric
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
  the same compute. (Relevant given the cost-control focus on the {{CLIENT_NAME}}/Scripius side.)
- **"What about pixel-perfect formatting / specific chart types?"** Tableau is still ahead on some of
  this. Name it honestly; show what AI/BI does well and where the trade-off lands.
- **"Does Genie make things up?"** It generates SQL you can inspect and correct; it only sees granted
  tables; feedback (Yes / Fix it / Request review) keeps a human in the loop.
