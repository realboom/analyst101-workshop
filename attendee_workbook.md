# Attendee Workbook — Analyst 101 Workshop

Welcome. This workbook is the **whole workshop**, start to finish: you'll take a **raw file** all the
way to a **governed table** in the no-code **Lakeflow Designer** (Part 0), then build an **AI/BI
dashboard** and ask questions in plain language with **Genie** on the shared dataset (Parts 1–4).
Follow along on your own screen, and ask questions any time. All data is synthetic — **no PHI**.

**Optional lens — coming from Tableau?** AI/BI isn't a one-to-one Tableau replacement, and that's
fine. If Tableau is your daily tool, keep the cheat-sheet below handy and note where this way of
working helps and where you'd stay in Tableau. If Tableau isn't your world, ignore those callouts.

## The dataset
Everything lives in `{{CATALOG}}.{{SCHEMA}}`:

| Table | What it is |
|---|---|
| `fact_encounters` | One row per patient encounter. ~80,000 rows over Jan 2023 to Dec 2025. Outcome flags: `readmitted_30d`, `mortality_flag`, `complication_flag`. |
| `dim_provider` | Providers, their specialty, and primary facility. |
| `dim_facility` | Hospitals and clinics, with type, city, state, region. |
| `dim_diagnosis` | ICD-10 codes with plain-language descriptions and clinical category. |
| `dim_procedure` | Procedure codes (incl. `{{PROCEDURE_CODE}}` {{PROCEDURE_EXAMPLE}}). |
| `dim_patient` | Patients with their assigned PCP and home facility (used for the PCP-continuity metric). |
| `dim_visit_type` | Visit type reference; non-standard types are excluded from PCP continuity. |

**Tableau translation cheat sheet** (keep this handy):

| Tableau | Databricks AI/BI |
|---|---|
| Workbook | Dashboard |
| Worksheet | Visualization widget |
| Published data source / LOD calc | Metric view (governed measures + dimensions) |
| Ask Data | Genie (natural-language querying) |
| Calculated field | Dataset column or dashboard calculated measure |
| Quick filter | Filter widget |
| Dashboard action | Cross-filtering (mostly automatic) |

## How AI/BI dashboards work (read this first)
An AI/BI dashboard has two tabs at the top, and this trips everyone up at first:

- **Data tab:** where you define **datasets** (SQL queries). A dataset is just the data. On its own it does not show anything on the canvas.
- **Canvas tab:** where you lay out the **visuals**. You add a visualization widget and point it at a dataset.

**The core loop you'll repeat all day:** define a dataset on the Data tab, then go to the Canvas tab and drop a visualization that reads from it.

**How to add any visualization (you'll do this constantly):**

- Go to the **Canvas** tab.
- Click **Add a visualization** and draw the box on the canvas.
- In the config panel on the right, set three things: the **Dataset** (which data), the **Visualization** type (table, bar, line, combo, heatmap, map, pivot, counter), and the **fields** (which columns go on the X axis, Y axis, color, rows, columns, or values). Each step below tells you exactly which fields to place where.

That's it. Everywhere below where it says "add a table" or "add a combo chart," that means this same loop.

> Note: field-well labels can differ slightly by visualization (X/Y for charts, Rows/Columns/Values for pivots and tables). If a label looks different, match it to the intent described.

---

> **Single-session Analyst 101?** Follow `agenda.md`: you'll do **Part 0** (ETL) plus **Parts 1–3**
> below and the **Genie** segment. **Parts 5–8** are the fuller advanced layout — use them if you
> have the time.

> **Capabilities we will cover:** the no-code medallion ETL build (Part 0), then rich interactive visuals (combo, heatmap, map, pivot, scorecard), calculated dimensions and measures, parameterized widgets, cross-filtering, drilling, forecasting and AI functions, multipage reporting, and Ask Genie from a published dashboard. The companion one-pager has a quick reference for each.

## Part 0 · Foundations & ETL — from a raw file to a governed table

Take a messy CSV a source system handed you and turn it into a clean, governed `dim_facility` table — **no code**, in the Databricks **Lakeflow Designer** visual ETL builder. Along the way you'll meet the building blocks every Databricks project uses: a **catalog**, a **schema**, a **volume**, and the **medallion (bronze → silver → gold)** pattern.

> You'll build everything into **your own schema**, which you create in Step 1, so you can click freely without stepping on anyone else. Pick a schema name based on your own name — **`{{CATALOG}}.analyst101_<your-name>`** (e.g. `analyst101_jsmith`). Everywhere below that says `analyst101_<you>`, use yours.

**The concepts (2 minutes, then we click).**

- **Catalog → Schema → Table** is just Databricks' three-level namespace, like *database server → database → table* elsewhere. Everything lives in **Unity Catalog**, which governs who can see and do what.
- **Volume** = a governed folder for **files** (CSVs, images, PDFs) that lives under a schema. It's where raw files land before they become tables.
- **Medallion architecture** is the industry-standard way to refine data in layers: **Bronze** = raw, as-ingested; **Silver** = cleaned and conformed (trimmed, typed, standardized, de-duplicated); **Gold** = business-ready, the table your dashboards and Genie actually use.

Today: **upload a raw facilities file → bronze → silver → gold `dim_facility`.**

**Step 1 · Create your schema and a Volume (in Catalog Explorer).** No code — so you get a feel for how Unity Catalog is organized. Everything you build lives in **your own** schema, which you'll own.

- **Create your schema:** left nav → **Catalog** → click the catalog **`{{CATALOG}}`** → **Create schema** (top-right) → name it **`analyst101_<you>`** (e.g. `analyst101_jsmith`), leave the default storage location, **Create**. *(If **Create schema** is greyed out, tell your instructor — the workshop group needs `CREATE SCHEMA` on `{{CATALOG}}`.)*
- **Create a `landing` volume:** open your new schema **`{{CATALOG}}.analyst101_<you>`** → **Create → Volume** → name it **`landing`**, leave it a **Managed volume**, **Create**. A volume is the governed home for files — where your raw file lands before it becomes a table.

**Step 2 · Upload the raw file.**

- Open your **`landing`** volume → **Upload to this volume** → choose the **`facilities_raw.<profile>.csv`** for your workshop (e.g. `facilities_raw.pediatric.csv`) — your instructor will share it, or download it from the workshop repo.
- Peek at it — it's *messy on purpose*: extra spaces, `State` spelled every which way (full name / code / different case), inconsistent `Type` capitalization, two rows with a **blank Region**, a **duplicate** facility row, and a trailing empty line. This is what real source extracts look like. Our job is to fix it.

**Step 3 · Open Lakeflow Designer (Visual Data Prep) and start a build.**

- Left nav → **Data Engineering → Visual Data Prep**. *(The Lakeflow Designer visual, no-code ETL builder — under Data Engineering you'll see **Runs**, **Data Ingestion**, and **Visual Data Prep**; pick the last one.)*
- Click **Create** (or **New**) to start a pipeline; name it **`facilities_medallion`**.
- You land on a **start screen** with a **Genie prompt box** and tiles (**Select a source**, **Upload a file**, **Load a sample**). From here there are **two ways to build** — pick one in Step 4: **Option A** — prompt Genie to build it (fast, AI-assisted), or **Option B** — build it by hand, one operator at a time.

**Step 4 · Build bronze → silver → gold — two ways.** You're turning the messy file into a clean 12-row `dim_facility`. Do it **either** way below — the transformations are the same; the difference is whether **Genie writes the steps for you** (A) or **you add them yourself** (B).

> Bronze → silver → gold here are **stages in one pipeline, not three separate tables.** Bronze is the raw read, silver is the cleaning/conforming, and the only table you save is the **gold** `dim_facility`.

- **Option A · Prompt Genie to build it (AI-assisted) — the fast way.** Choose **Select a source** and point at your `landing` volume's `facilities_raw.<profile>.csv`. In the **Genie prompt box**, describe the outcome in plain English, e.g.:
  > Clean this facilities CSV into a table called **dim_facility**. Trim whitespace on all text columns. Standardize **State** to a 2-letter US state code (e.g. Utah → UT). Proper-case **Type**. Drop rows where **Facility ID** is blank. Remove duplicate rows by **Facility ID**. Fill any blank **Region** from another facility in the same **City**. Rename columns to snake_case: facility_id, facility_name, facility_type, city, state, region.

  **Review the steps Genie generated** — each shows a live preview; tweak anything off. Set the output to a **Table** named **`dim_facility`** in **`{{CATALOG}}.analyst101_<you>`**, mode **Create/replace**, then **Run**. *(Table type — a materialized view isn't needed and may not be available everywhere. Create/replace rebuilds the full table each run; merge/append are for incremental loads.)*

- **Option B · Build it by hand (operator by operator) — the manual way.**
  - **Bronze — bring the raw file in as-is:** **Select a source** → `{{CATALOG}}.analyst101_<you>.landing` → `facilities_raw.<profile>.csv`. Confirm it parsed into columns (`Facility ID`, `Facility Name`, `Type`, `City`, `State`, `Region`). Leave everything raw — you should see ~13 rows (the dupe and blank line are still here; expected).
  - **Silver — clean and conform** (add transforms one at a time; each shows a live preview): (1) **Trim whitespace** on the text columns. (2) **Standardize `State` to a 2-letter code** — uppercase, then map full names to codes (`UTAH→UT`, `CALIFORNIA→CA`). (3) **Proper-case `Type`** (so `pediatric clinic` / `PEDIATRIC CLINIC` → `Pediatric Clinic`). (4) **Drop empty rows** — filter where `Facility ID` is null/blank. (5) **De-duplicate** on `Facility ID` (standardize *first*, so the duplicate is a true dupe by now). → **12 clean rows**, but two still have a blank `Region`.
  - **Gold — make it business-ready `dim_facility`:** (1) **Fill the missing `Region`** from a same-`City` sibling — a window/group step taking `MAX(Region)` **partitioned by `City`**, where `Region` is blank. (2) **Rename to snake_case** (`Facility ID→facility_id`, etc.). (3) **Set the output** to a **Table** named **`dim_facility`** in **`{{CATALOG}}.analyst101_<you>`**, mode **Create/replace**, then **Run**.

- **Option C · Short on time? Do it in a notebook (code).** If the visual build won't fit the session — or an analyst prefers code — open **`notebooks/01_etl_notebook_alternative.py`**, attach **serverless**, set the widgets to your `catalog`, your `schema`, and the `profile` you uploaded, and run its **three cells**: (1) **explore** the raw CSV straight from SQL with **`read_files()`**, (2) load it into a `facilities_raw` **temp view**, (3) clean it with **Spark SQL** into `dim_facility`. Same raw file in your `landing` volume, same bronze → silver → gold logic, same **12-row** result — just code instead of the visual canvas. It writes the identical `dim_facility`, so **Steps 5–6 below apply either way.**

**Step 5 · Verify + the governance payoff.**

- Back in **Catalog**, open `{{CATALOG}}.analyst101_<you>.dim_facility`. Confirm **12 rows**, clean `state` codes, proper-cased `facility_type`, and **no blank regions**.
- Open the **Lineage** tab — you'll see **`facilities_raw.<profile>.csv` (volume) → `dim_facility` (table)**. UC lineage tracks *persisted objects*, so the bronze→silver→gold steps live **inside the pipeline** (open the operator graph in Visual Data Prep to see them). No code, and a governed, fully-lineaged pipeline you could schedule nightly.

**Step 6 · Make it Genie-ready — add comments and a key.** This is what makes your table *usable by Genie and the AI/BI Assistant* later. **The setup drives the answer:** table and column comments plus a declared key are the **context** these AI tools read — a well-annotated table gets good answers; a raw one gets guesses. Run this in a SQL editor or a notebook cell (or set the same comments in Catalog Explorer's UI):

```sql
COMMENT ON TABLE {{CATALOG}}.analyst101_<you>.dim_facility IS 'Hospitals and clinics with type, city, state, and region. One row per facility.';

ALTER TABLE {{CATALOG}}.analyst101_<you>.dim_facility ALTER COLUMN facility_id SET NOT NULL;
ALTER TABLE {{CATALOG}}.analyst101_<you>.dim_facility ADD CONSTRAINT pk_dim_facility PRIMARY KEY (facility_id);

ALTER TABLE {{CATALOG}}.analyst101_<you>.dim_facility ALTER COLUMN facility_id   COMMENT 'Primary key. Unique identifier for the facility.';
ALTER TABLE {{CATALOG}}.analyst101_<you>.dim_facility ALTER COLUMN facility_name COMMENT 'Hospital or clinic name.';
ALTER TABLE {{CATALOG}}.analyst101_<you>.dim_facility ALTER COLUMN facility_type COMMENT 'Facility type (e.g., hospital, clinic, urgent care).';
ALTER TABLE {{CATALOG}}.analyst101_<you>.dim_facility ALTER COLUMN city          COMMENT 'City where the facility is located.';
ALTER TABLE {{CATALOG}}.analyst101_<you>.dim_facility ALTER COLUMN state         COMMENT 'Two-letter state code.';
ALTER TABLE {{CATALOG}}.analyst101_<you>.dim_facility ALTER COLUMN region        COMMENT 'Business region grouping for the facility.';
```

- Reopen the table in **Catalog** — every column now has a description and `facility_id` is a primary key. That's the same treatment the **shared** tables ship with (open one and compare the comments + keys). In **Part 4** you'll point Genie at *this* table — and this annotation is exactly why it can answer facility questions reliably.

> **What you just did:** turned a raw file into a governed, business-ready table with a repeatable no-code pipeline — then **annotated it so AI tools can read it**. This is the same kind of well-documented table the AI/BI dashboards and Genie use in the rest of the workshop. *(Databricks Day goes deeper on this: the setup — clean tables, precise comments, explicit joins, tight scope — is what drives a trustworthy answer, not a clever prompt.)*

---

## Part 1 - The dataset is your analytics engine (window functions, ranking, period-over-period)

The key idea: a dataset is **full Databricks SQL**. The things you do with table calcs, LOD expressions, and rank in Tableau are just window functions here, defined once in the dataset and reused by every widget. We'll go straight to the kind of analysis you actually do.

**Step 1 · Create the dashboard.**

- In the left nav, click **Dashboards**, then **Create dashboard**. Name it "My Analyst 101 Workshop".
- You'll open on the **Canvas** tab, with a **Data** tab right next to it at the top.

**Step 2 · Create the `Provider performance` dataset.** This ranks providers by risk outcome with a percentile and quartile (min 200 encounters).

- Go to the **Data** tab and click **Create from SQL**.
- Paste the query below, click **Run** to preview the rows, and name the dataset `Provider performance`.

```sql
WITH prov AS (
  SELECT p.provider_name, p.specialty, COUNT(*) AS enc,
         AVG(e.readmitted_30d)*100 AS readmit_rate,
         AVG(e.complication_flag)*100 AS comp_rate,
         AVG(e.length_of_stay_days) AS avg_los
  FROM {{CATALOG}}.{{SCHEMA}}.fact_encounters e
  JOIN {{CATALOG}}.{{SCHEMA}}.dim_provider p USING (provider_id)
  GROUP BY p.provider_name, p.specialty
  HAVING COUNT(*) >= 200
)
SELECT provider_name, specialty, enc,
       ROUND(readmit_rate,1) AS readmit_rate_pct,
       ROUND(comp_rate,1)    AS comp_rate_pct,
       ROUND(avg_los,1)      AS avg_los_days,
       ROUND(PERCENT_RANK() OVER (ORDER BY readmit_rate),2) AS readmit_pctile,
       NTILE(4) OVER (ORDER BY readmit_rate) AS readmit_quartile
FROM prov
```

**Step 3 · Put it on the canvas as a table (provider scorecard).**

- Go to the **Canvas** tab and click **Add a visualization**.
- **Dataset:** `Provider performance`. **Visualization:** Table.
- **Columns to show, left to right:** `provider_name`, `specialty`, `enc`, `readmit_rate_pct`, `comp_rate_pct`, `avg_los_days`, `readmit_pctile`, `readmit_quartile`. (Remove any columns you don't want; drag to reorder.)
- **Rename headers** for readability, e.g. Provider, Specialty, Encounters, Readmit %, Complication %, Avg LOS (days), Readmit percentile, Quartile.
- **Sort:** `readmit_rate_pct` descending (worst readmission at top).
- **Conditional formatting:** color `readmit_quartile` on a scale where 1 is green and 4 is red (quartile 1 = lowest readmission = best; quartile 4 = highest = worst). Or apply a red-to-green color scale directly on `readmit_rate_pct`.
- Result: a ranked, risk-binned provider scorecard, with no table-calc plumbing.

**Step 4 · Create the `Outcome trend` dataset and add a combo chart.** This is period-over-period with a rolling average (LAG + a windowed AVG).

- **Data** tab → **Create from SQL** → paste the query below → name it `Outcome trend`.

```sql
WITH m AS (
  SELECT DATE_TRUNC('month', admit_date) AS month, COUNT(*) AS encounters,
         AVG(readmitted_30d)*100 AS readmit_rate
  FROM {{CATALOG}}.{{SCHEMA}}.fact_encounters
  GROUP BY 1
)
SELECT month, encounters,
       encounters - LAG(encounters,1) OVER (ORDER BY month) AS mom_change,
       ROUND(AVG(encounters) OVER (ORDER BY month ROWS BETWEEN 2 PRECEDING AND CURRENT ROW),0)
             AS rolling_3mo,
       ROUND(readmit_rate,1) AS readmit_rate_pct
FROM m
```

- **Canvas** tab → **Add a visualization**. **Dataset:** `Outcome trend`. **Visualization:** Combo (bar + line).
- **X axis:** `month`.
- **Bars (left/primary Y):** `encounters`.
- **Line (right/secondary Y):** `rolling_3mo` (the smooth trend line).
- **Sort:** X axis ascending by `month`.

**Step 5 · Add calculated fields (no code).** You don't have to do everything in SQL — you can add calculated fields right on a dataset, just like a Tableau calculated field. We'll build an **age band** and look at **cost by age band** (charges vs. what was actually paid).

A field that bins a row needs **row-level** columns, so first build a small dataset on `fact_encounters`:

- **Data** tab → **Create from SQL** → paste the query below → name it `Cost by patient`.

```sql
SELECT patient_age, total_charges, total_paid, readmitted_30d
FROM {{CATALOG}}.{{SCHEMA}}.fact_encounters
```

- **Calculated dimension — `age_band`.** On the `Cost by patient` dataset, add a **calculated dimension** that bins `patient_age` with a CASE. Use the band that fits your population:
  - **Adult:** `CASE WHEN patient_age < 40 THEN '<40' WHEN patient_age < 65 THEN '40-64' ELSE '65+' END`
  - **Pediatric:** `CASE WHEN patient_age < 1 THEN '<1 (infant)' WHEN patient_age < 5 THEN '1-4' WHEN patient_age < 13 THEN '5-12' ELSE '13-18' END`
- **Calculated measures — average cost.** On the same dataset, add two **calculated measures**: `avg_charges` = `AVG(total_charges)` and `avg_paid` = `AVG(total_paid)`. *(Optional combined measure: `AVG(total_charges - total_paid)` = the average unpaid gap per encounter.)*
- **Put it on the canvas.** Add a **Bar** chart. **X axis:** `age_band`. **Y axis:** `avg_charges` and `avg_paid` (two bars per band). Now you can see how charged vs. paid amounts move across age bands — and it recomputes automatically as filters change.

> **Tableau translation:** `PERCENT_RANK` / `NTILE` replace your rank table calcs; `LAG` and the windowed `AVG` replace the running/difference table calcs and the trailing-average trick; the calculated measure/dimension is your calculated field. They live in the dataset, governed and reusable, instead of per-worksheet.

---

## Part 2 - Advanced visuals, parameters, and benchmarks

Same loop as before (Data tab to define, Canvas tab to visualize). This part adds interactivity and the richer chart types. Each step lists exactly which fields to place where.

**Step 1 · Parameterized widget (like a Tableau parameter).**

- Add a dashboard **parameter** named `min_encounters` (type: whole number, default `200`).
- Edit the `Provider performance` dataset and change the HAVING line to reference it:

```sql
HAVING COUNT(*) >= :min_encounters
```

- Add the **parameter widget** to the canvas and bind it to `min_encounters`. Now the scorecard table re-thresholds live as you change the value.

**Step 2 · Benchmark vs peer group (a window over a grouped aggregate).**

- **Data** tab → **Create from SQL** → name it `Facility vs region`.

```sql
SELECT f.region, f.facility_name,
       ROUND(AVG(e.readmitted_30d)*100,1) AS rate_pct,
       ROUND(AVG(e.readmitted_30d)*100
             - AVG(AVG(e.readmitted_30d)*100) OVER (PARTITION BY f.region),1) AS vs_region_avg_pts
FROM {{CATALOG}}.{{SCHEMA}}.fact_encounters e
JOIN {{CATALOG}}.{{SCHEMA}}.dim_facility f USING (facility_id)
GROUP BY f.region, f.facility_name
```

- **Add a visualization.** **Dataset:** `Facility vs region`. **Visualization:** Table.
- **Columns, left to right:** `region`, `facility_name`, `rate_pct`, `vs_region_avg_pts`.
- **Sort:** `vs_region_avg_pts` descending.
- **Conditional formatting:** diverging scale on `vs_region_avg_pts` centered at 0. Since higher readmission is worse, color positive values (above the region average) red and negative values (below the region average) green. Instantly shows which facilities run hot or cold versus their region.

**Step 3 · Heatmap.**

- **Data** tab → **Create from SQL** → name it `Category x region`.

```sql
SELECT d.clinical_category, f.region,
       ROUND(AVG(e.complication_flag)*100,1) AS comp_rate_pct, COUNT(*) AS enc
FROM {{CATALOG}}.{{SCHEMA}}.fact_encounters e
JOIN {{CATALOG}}.{{SCHEMA}}.dim_facility f USING (facility_id)
JOIN {{CATALOG}}.{{SCHEMA}}.dim_diagnosis d ON e.primary_icd10_code = d.icd10_code
GROUP BY d.clinical_category, f.region
```

- **Add a visualization.** **Dataset:** `Category x region`. **Visualization:** Heatmap.
- **X axis (columns):** `region`.
- **Y axis (rows):** `clinical_category`.
- **Color:** `comp_rate_pct` (darker = higher complication rate).
- **Tooltip (optional):** `enc`.

**Step 4 · Map.**

- **Data** tab → **Create from SQL** → name it `By state`.

```sql
SELECT f.state, COUNT(*) AS enc, ROUND(AVG(e.readmitted_30d)*100,1) AS readmit_rate_pct
FROM {{CATALOG}}.{{SCHEMA}}.fact_encounters e
JOIN {{CATALOG}}.{{SCHEMA}}.dim_facility f USING (facility_id)
GROUP BY f.state
```

- **Add a visualization.** **Dataset:** `By state`. **Visualization:** Choropleth map (US states).
- **Location / geography:** `state` (two-letter state code).
- **Color:** `readmit_rate_pct`.
- **Tooltip (optional):** `enc`.

**Step 5 · Pivot table.**

- **Data** tab → **Create from SQL** → name it `Category x encounter type`.

```sql
SELECT d.clinical_category, e.encounter_type, COUNT(*) AS enc
FROM {{CATALOG}}.{{SCHEMA}}.fact_encounters e
JOIN {{CATALOG}}.{{SCHEMA}}.dim_diagnosis d ON e.primary_icd10_code = d.icd10_code
GROUP BY d.clinical_category, e.encounter_type
```

- **Add a visualization.** **Dataset:** `Category x encounter type`. **Visualization:** Pivot.
- **Rows:** `clinical_category`.
- **Columns:** `encounter_type`.
- **Values:** `enc` (aggregate: Sum).

**Step 6 · Forecasting and AI functions.** Project the next six months of volume with the built-in `ai_forecast` function.

- **Data** tab → **Create from SQL** → name it `Volume forecast`.

```sql
WITH monthly AS (
  SELECT DATE_TRUNC('month', admit_date) AS ds, COUNT(*)::DOUBLE AS y
  FROM {{CATALOG}}.{{SCHEMA}}.fact_encounters
  GROUP BY 1
)
SELECT ds, y AS encounters, NULL AS forecast, NULL AS lower, NULL AS upper FROM monthly
UNION ALL
SELECT ds, NULL, y_forecast, y_lower, y_upper
FROM AI_FORECAST(TABLE(monthly), horizon => '2026-06-01', time_col => 'ds', value_col => 'y')
```

- **Add a visualization.** **Dataset:** `Volume forecast`. **Visualization:** Line.
- **X axis:** `ds`.
- **Lines (Y):** `encounters` (actuals) and `forecast` (projection). The actuals line stops where the forecast begins, which is expected.
- **Confidence band (optional):** `lower` and `upper` as a shaded range around `forecast`.
- Other built-in AI functions you can call the same way in SQL: `ai_query`, `ai_classify`, `ai_extract`, `ai_summarize`.

**Step 7 · Interactivity: filters, cross-filtering, drill.**

- **Filter widget:** Add a visualization → choose **Filter**. Set the field to `region`, and connect it to the widgets whose datasets contain `region` (the `Facility vs region` table and the `Category x region` heatmap). Selecting a region updates those widgets.
- **Cross-filter:** click a bar, cell, or row in any chart and watch the other widgets on the page filter to match (like a Tableau dashboard action, no setup).
- **Drill-down:** on a chart, add a hierarchy `region` then `facility_name` then `provider_name`, and click to drill a level at a time.

**Step 8 · Multipage reporting.**

- Use the **page tabs** at the top of the canvas (next to the current page name) to add pages, then drag widgets onto each. Suggested split: **Overview** (KPIs + trend + forecast), **Provider performance** (the scorecard + parameter), and **Geography** (map + region benchmark). Filters can be shared across pages.

**Step 9 · Themes (optional).**

- In dashboard settings you can apply a **theme** (colors, fonts) for a branded look. We're not focusing on branding today, but it's there for when you share externally.

> **Honest trade-off:** Tableau is still ahead on a few things: very fine-grained reference lines/bands, some niche chart types, and certain LOD nuances. The counter that matters for you: rich interactive visuals, cross-filtering, drilling, parameters, calculated fields, forecasting, and multipage reports are all here, and anything you can express in SQL is first-class, so you're rarely boxed in.

---

## Part 3 - Build with AI: the assistant and the semantic layer

**Step 1 · AI-assisted authoring.**

- On the canvas, click **Add a visualization**, then use the **Assistant** (the sparkle icon) and type a plain-English request, for example "Show average length of stay by specialty as a bar chart," or "Complication rate by clinical category."
- Accept the result, then tweak it. You can open and edit the underlying SQL if you want exact control.

**Step 2 · Metric views (the semantic layer).**

- This is the equivalent of a Tableau published data source. Measures (like readmission rate) and dimensions are defined once, governed, and reused everywhere, so everyone's numbers match. Your instructor will show one.

> **Why it matters:** define "readmission rate" once and every dashboard and Genie answer uses the same definition. No more slightly different numbers across analysts.

**Step 3 · Publish your dashboard.**

- Click **Publish** (top right) to publish the dashboard you just built — it's now shareable with your team, and everyone sees the same governed numbers.

---

## Part 4 - Build a Genie Agent

Now the fun part. Your dashboard is published — and a published dashboard already has an **Ask Genie** box at the bottom for quick questions on just that data. Here you'll build the full **Genie Agent** (this is what used to be called a "Genie space") on the same data, give it a few instructions, and ask questions in plain language.

**Step 1 · Create a Genie Agent — on the shared tables (plus your own `dim_facility`, if you built one).**

- In the left sidebar, click **Genie Agents** → **New** (top-right). *(If your workspace still says "Genie" / "Genie spaces," it's the same thing.)*
- Add these **data sources** (click **+ Add data** / the table picker):
  1. From the **shared** schema `{{CATALOG}}.{{SCHEMA}}`: **`fact_encounters`**, **`dim_provider`**, **`dim_diagnosis`**, **`dim_procedure`**.
  2. **`dim_facility`** — use the **shared** `{{CATALOG}}.{{SCHEMA}}.dim_facility`. **⭐ If you built your own in Part 0**, add **`{{CATALOG}}.analyst101_<you>.dim_facility`** instead (and **don't** also add the shared one) — it has the same 12 facilities and `facility_id`s, so either one joins to `fact_encounters` cleanly.
- Click **Create**. Your Genie Agent is created — you'll add instructions and trusted assets in its **Configuration** next.

> **If you used your own `dim_facility`, this closes the loop:** the raw file you cleaned into a governed table back in Part 0 is now the facility dimension powering your Genie Agent — ask a facility- or region-level question (below) and Genie answers straight off *your* table.

**Step 2 · Add instructions.**

- Click **Configure** (top-right of the Genie Agent) to open the agent's **Configuration**.
- In the **Configuration** (the agent's **Instructions** area), paste the block below (your instructor also shares it). Save.

Instructions block to paste (scope + conventions only — no join prose: relationships and the example query carry the joins):
```
This Genie Agent answers questions about synthetic hospital encounters. There is no PHI.

Conventions:
- Express all rates as a percentage from 0 to 100, rounded to one decimal; currency as whole dollars.
- When ranking providers or facilities by a rate, only include those with at least 200 encounters
  unless the user asks otherwise.
- Show plain-language names in results (provider_name, facility_name, region, clinical_category,
  procedure_description), not the id columns.
```
> *Why no "data model / joins" here:* the shared tables' joins are already declared as foreign keys, and the example query (Step 3) shows the `dim_facility` join — so restating joins in prose is redundant. Text instructions are a last resort; relationships and examples are more reliable. The only non-declared join (shared `fact_encounters` → your own `dim_facility`) is covered by the example query + your PK from Part 0 Step 6; if a facility question ever misses, define it as an explicit **relationship** in the **Configuration**, not in text.

**Step 3 · Add SQL-based context — this is what really tunes Genie Agent.** Free text is the *last* resort; **SQL-based context is more reliable**.

- **Synonyms** — map jargon and abbreviations to a **column** (synonyms attach to columns, not tables).
  - **First, ask it cold — before you add any synonym:** *"Which providers have the highest bounce-back rate, with at least 200 encounters?"* Genie still answers — but watch it **flag the guess**: *"I interpreted bounce-back rate as the 30-day readmission rate…"* It's inferring `bounce-back` → `readmitted_30d` and telling you it's inferring. Fine for one analyst who reads the caveat; risky once the whole org trusts the number.
  - **Now pin it.** In the **Configuration** → the data source → **Edit column metadata** → pick the column → **Synonyms** field. Add each of these:
    - `dim_provider.provider_name` ← **doctor**, **physician**
    - `dim_facility.facility_name` ← **hospital**, **clinic**, **site**
    - `fact_encounters.length_of_stay_days` ← **LOS**, **length of stay**
    - `fact_encounters.readmitted_30d` ← **readmission**, **readmit**, **bounce-back**
    - `fact_encounters.total_paid` ← **reimbursement**, **amount paid**
  - **Ask the same question again** — the caveat is gone: `bounce-back` is now a known mapping, not a guess. Everyday words like *"which doctors have the most encounters?"* and *"average LOS by hospital"* resolve too, without anyone knowing the column names.

  > **Synonyms aren't for words Genie already knows** — it maps "doctor" → `provider_name` on its own. They're for **jargon and abbreviations** an LLM would otherwise *guess* at ("bounce-back," internal acronyms). The win usually isn't a different answer — it's the **same answer with the guesswork (and the caveat) removed**, so no one downstream is trusting an inference.
- **SQL expressions** — reusable, named metrics/filters. In the **Configuration** → the agent's **Instructions** → **add a SQL expression**; for each, give a **name**, paste the **SQL**, and mark it a *measure* or *filter*. Add:
  - measure **`readmission_rate`** = `AVG(readmitted_30d) * 100`
  - filter **`inpatient_only`** = `encounter_type = 'Inpatient'`

  Now *"readmission rate by facility, inpatient only"* uses your governed definitions — same math every time, no re-deriving. *(Fuller set — `complication_rate`, `mortality_rate`, `avg_los` — is in `genie/genie_space_config.md`.)*
- **An example query** — teach one full, validated answer. Add the question *"30-day readmission rate by facility, min 200 encounters"* with this SQL:
  ```sql
  SELECT f.facility_name, ROUND(AVG(e.readmitted_30d)*100,1) AS readmit_rate_pct, COUNT(*) AS encounters
  FROM fact_encounters e JOIN dim_facility f USING (facility_id)
  GROUP BY f.facility_name HAVING COUNT(*) >= 200 ORDER BY readmit_rate_pct DESC
  ```
  *Note the example spells out `AVG(readmitted_30d)*100` rather than referencing the `readmission_rate` expression above. An example query must be complete, runnable SQL — a SQL expression is context Genie reads, not a column/function you can name in a query. Keep the two in sync (same math). This is the opposite of the metric views / SQL functions in Parts 5–8, which **are** real objects you call by name — `MEASURE(...)` / `pcp_continuity_by_provider()`.*

> **Priority order (what Genie reads, best first):** column comments/keys → **synonyms** → **SQL expressions** (metrics/filters) → **example queries** → free-text instructions *last*. The full set is in `genie/genie_space_config.md`.

**Step 4 · Ask a few questions.** Try these, then your own:

- "How many encounters were there in 2024 by region?" — *`region` comes from the `dim_facility` you built.*
- "Which **providers** have the highest bounce-back rate, with at least 200 encounters?" — *the Step 3 question again — no caveat now that `bounce-back` is pinned.*
- "Which facilities have the highest 30-day readmission rate, with at least 200 encounters?" — *your `dim_facility` + the example query you just added.*
- "What is the average length of stay for a {{PROCEDURE_EXAMPLE}}?"

**Step 5 · Show the SQL.** On any answer, click **Show generated code** to see the Databricks SQL Genie wrote — for the facility/region questions you'll see it joining `fact_encounters` to *your* `analyst101_<you>.dim_facility`.

> **Why this works — the setup drives the answer.** Genie's quality comes from the *setup*, not clever prompting. The context it reads is: **well-annotated tables** (every column commented), **explicit joins and keys**, and a **tight scope** (≤5 well-modeled tables — the shared ones plus your `dim_facility`). That's why the shared tables just work — and it's exactly why you annotated your own `dim_facility` in **Part 0, Step 6**. Curated, documented tables beat raw wide ones. *(This is the Databricks Day theme — "maturing Genie": engineer accuracy into the setup, then pin the known-good answers.)*
>
> **For the SQL folks:** Genie writes Databricks SQL, so it's a fast way to see the correct syntax and functions when you translate from what you write today. Copy it and build on it.
>
> **Trust:** every answer shows its SQL, Genie only sees tables you've been granted, and you can give feedback (Yes / Fix it / Request review). It's a fast first draft, not a black box.

---

# Advanced features: governed metrics & trusted assets

Parts 0–4 took you from a raw file to dashboards and a Genie Agent — *fast* answers. This half is the **accuracy layer**: making answers *trustworthy*. It's the same arc as the Databricks Day session — the **confidence stack**, highest-confidence first:

1. **SQL functions** — deterministic, callable, audited logic.
2. **Metric views** — one governed definition of a metric, referenced by name everywhere.
3. **Trusted assets in Genie** — plain-language questions resolve to those governed definitions instead of ad-hoc SQL.

Everything runs on the **PCP continuity** use case, already built on the shared schema. *PCP continuity = the share of a patient's **standard** visits handled by their **assigned PCP** — a real quality measure with real business rules (standard visits only; attending must equal the assigned PCP). Those rules are exactly why it needs governing.* You'll **use** the pre-built assets first (Parts 5–7), then see how to **author your own** (Part 8).

## Part 5 - SQL functions: deterministic, callable logic

> **Parts 5 and 6 are exploratory.** The function and metric view already exist in the shared schema — here you just *run queries against them* to see how governed assets behave. You'll build your own versions in **Part 8**.

A SQL function packages logic once, so anyone — including Genie — calls it **by name** instead of re-deriving joins. It's registered in Unity Catalog and governed (grant `EXECUTE`; callers can't see or change the logic inside — ideal for PHI-sensitive clinical rules). We use **one** function here — `pcp_continuity_by_provider()` — because it does the **provider grain the metric view can't** (the overall/facility/region ratio is covered by the metric view in Part 6). Run it in a SQL editor:

```sql
-- table function: continuity BY PROVIDER, min 200 standard visits
-- (the provider grain the metric view can't produce)
SELECT provider_name, standard_visits, ROUND(continuity_ratio*100,1) AS continuity_pct
FROM {{CATALOG}}.{{SCHEMA}}.pcp_continuity_by_provider()
WHERE standard_visits >= 200
ORDER BY continuity_ratio DESC;
```

It's a **table function** — you query it like a table, but the provider-grain logic lives in one governed place, not re-derived per query. Same inputs → same result every time (**deterministic**).

> **When do you reach for a function instead of the metric view?** When the question needs a **grain the metric view doesn't model**. The metric view (Part 6) rolls up by facility / region / month — it has **no provider dimension** — so *continuity by provider* is a job only the function can do. That's the clean division of labor: metric view for governed rollups, functions for the grains (and parameterized logic) it can't express.
>
> **A note on Genie + functions — this is a Part 7 concern, not something to set up here.** Right now (Part 5) you're just calling the function in a SQL editor, where it's fully deterministic. *Inside* Genie it behaves differently, and you'll deal with that when you build the agent in **Part 7**: Genie tends to prefer the metric view for anything it can answer that way, so adding the function (or a text instruction to use it) is **not** enough to make Genie call it. The fix, in Part 7, is to add an **example query** whose SQL calls the function (Configure → Examples → Add → Example Query) — and the **provider-grain question is where you test it**. Tested: pairing *"which providers have the lowest PCP continuity?"* to a `pcp_continuity_by_provider()` example query made Genie call the function; without it, Genie forced the question through the metric view (which has no provider dimension) and returned nothing.

## Part 6 - Metric views: one metric, one number

A **metric view** defines a measure **once**, in Unity Catalog, so every dashboard, notebook, and Genie Agent computes it identically. `pcp_continuity_metrics` is already built. Query its measures with `MEASURE()` and group by its dimensions:

```sql
-- continuity by facility
SELECT `Facility`,
       ROUND(MEASURE(`PCP Continuity Ratio`)*100,1) AS continuity_pct,
       MEASURE(`Total Standard Visits`)             AS visits
FROM {{CATALOG}}.{{SCHEMA}}.pcp_continuity_metrics
GROUP BY `Facility`
ORDER BY continuity_pct DESC;
```

Now change **one line** — ``GROUP BY `Region` `` or ``GROUP BY `Encounter Month` `` — and the *same* measure re-slices correctly, no re-deriving:

```sql
SELECT `Region`, ROUND(MEASURE(`PCP Continuity Ratio`)*100,1) AS continuity_pct
FROM {{CATALOG}}.{{SCHEMA}}.pcp_continuity_metrics
GROUP BY `Region` ORDER BY continuity_pct DESC;
```

> **Why this matters (query-time grouping):** continuity is a **ratio** — it's *non-additive*, so averaging facility ratios does **not** give the regional ratio. A metric view resolves the grouping **at query time** from the underlying counts, so the number is mathematically correct at every grain. That's the trap a copy-pasted calculated field falls into — and the reason to define it once, centrally.

## Part 7 - Trusted assets in Genie + the benchmark

Now wire the governed definitions into Genie so plain-language questions resolve to them.

**First, see the problem — best-effort is phrasing-sensitive.** On a *bare* agent (no trusted asset), ask the same thing two ways and click **Show generated code** each time:
- *"What is our overall PCP continuity rate?"* → Genie restricts to standard (office) visits → **76.3%** ✅
- *"What share of visits are with the patient's PCP?"* → Genie counts **all** visit types → **65.5%** ❌

Same question, an **11-point swing** by wording. Genie isn't "dumb" here — from the phrasing it inferred the standard-visits rule on the first one but not the second — and **nothing in the data forces it** (the standard-visits rule lives only in the governed assets, not as a flag on the tables). That's the trust problem: two analysts phrase it differently and report two different numbers.

**Now anchor it to a governed definition — in two parts, because both matter:**
1. **Add the governed assets to the agent.** Click **Configure**, go to the agent's **data sources**, click **Add**, and add the existing metric view **`pcp_continuity_metrics`** and the function **`pcp_continuity_by_provider`** (for provider-level questions). *(Adding them makes them available — but on its own, Genie often still hand-writes its own SQL. The routing instruction below is what makes it actually use them.)*
2. **Point Genie at them with an instruction** (this is the step people skip). In **Instructions**, add a *routing* instruction — not the calculation itself:
   > *For PCP continuity, use the governed assets rather than hand-writing SQL: query the `pcp_continuity_metrics` metric view with `MEASURE()` (e.g. ``MEASURE(`PCP Continuity Ratio`)``), or call `pcp_continuity_by_provider()` for provider-level questions. They already encode the definition.*

   *Note what this instruction does **not** contain: the standard-visits/assigned-PCP rules. Those live in the metric view and function — restating them here would be redundant and would just hand Genie the recipe to hand-write the logic instead of calling the governed asset. Route to the asset; let the asset own the definition.*

Now ask the continuity question, any phrasing, and **Show generated code**: Genie calls ``MEASURE(`PCP Continuity Ratio`)`` **by name** and returns **76.3%** — even for wordings that gave the naive agent 65.5%. *(In our testing, registering the asset alone left Genie hand-writing SQL; adding the instruction flipped it to call the metric view by name on every phrasing. The registration makes it available; the instruction makes it preferred.)*

**One more lever — the provider question needs an example query.** Steps 1–2 anchor the *rate* question to the metric view. The provider-grain question is different: Genie prefers the metric view and generally **won't call `pcp_continuity_by_provider()` on its own** — even for *"which providers have the lowest continuity?"*, which the metric view can't answer (it has no provider dimension). Registering the function and the routing instruction is **not** enough; give Genie an **example query**: click **Configure**, go to the agent's **Examples**, click **Add**, and select **Example Query**, then enter the question and paste the SQL:
- Question: *"Which providers have the lowest PCP continuity, with at least 200 standard visits?"*
- SQL:
  ```sql
  SELECT provider_name, standard_visits, ROUND(continuity_ratio*100,1) AS continuity_pct
  FROM {{CATALOG}}.{{SCHEMA}}.pcp_continuity_by_provider()
  WHERE standard_visits >= 200 ORDER BY continuity_ratio ASC
  ```

Now ask that provider question and **Show generated code** — Genie calls the function. *(Tested: without the example query, Genie forced the question through the metric view and returned nothing.)* This is the escalation ladder: **register → instruct → example query**, escalating until Genie uses the asset — a function usually needs the example query; the metric view often just needs the instruction.

> **The honest mechanism** (matches the docs): Genie is **nondeterministic** even with trusted assets — it *decides* whether to call the function/query or just learn the rule from it. So the badge isn't guaranteed on every ask. What *is* reliable is the **single governed definition**: the metric view and function define continuity **once**, in Unity Catalog. Call them directly (SQL, dashboards) and you get the **same number every time, by definition** — that's the real determinism. In Genie they act as an **anchor** so answers converge on the governed number instead of drifting by phrasing like the naive agent. To *maximize* Genie using the asset (and showing the badge), also add it as a **parameterized example query** tied to a representative question.

**Make it repeatable — the Benchmark and Monitor tabs.** The two-phrasing test above is the idea done *by hand*. Two tabs at the top of the agent turn it into something you can measure and curate over time.

### Benchmark — quantify the accuracy

A benchmark is a set of *question → expected-SQL* pairs. On **Run**, Genie answers each question its own way, executes both its SQL and your expected SQL, and scores whether they match — so you get a number, not a vibe.

**Set it up:**

1. Open your Genie agent and click **Benchmark** at the top of the agent.
2. Click **+ Add benchmark**, then enter the **question** and the **SQL**. Add all three below. *(Benchmarks 2 and 3 use the **same** expected SQL on purpose — two phrasings of "the rate," one governed answer; that's how you prove the phrasing drift is gone.)*

   **Benchmark 1 — facility ranking**
   - Question: `Which facilities have the lowest PCP continuity, and how many standard visits do they have?`
   - SQL:
     ```sql
     SELECT
       `Facility`,
       MEASURE(`PCP Continuity Ratio`) AS pcp_continuity_ratio,
       MEASURE(`Total Standard Visits`) AS total_standard_visits
     FROM
       {{CATALOG}}.{{SCHEMA}}.pcp_continuity_metrics
     GROUP BY
       `Facility`
     ORDER BY
       pcp_continuity_ratio ASC
     ```

   > **Expect Benchmark 1 to score _Bad_ — and that's the point.** "Which facilities have the **lowest**…" reads as a *top-N*, so Genie adds an `ORDER BY … LIMIT` and returns just the bottom few; your ground truth returns **all 12**. The scorer compares result sets exactly, so a different **shape** = Bad — even though every continuity value Genie returned is the **governed 76.3%-definition** number. This is a *shape/intent* mismatch, **not** a governance break: the metric is pinned, only the row count differs. The takeaway — benchmark scoring is strict exact-match, so your ground-truth SQL has to encode the answer *shape* you mean, and a fuzzy superlative like "lowest" forces you to decide what "the answer" is (all facilities ranked, or just the bottom N?). Benchmarks 2 and 3 below score **Good** — that's where you prove the phrasing drift on *the number* is gone.

   **Benchmark 2 — "share of visits with the PCP"**
   - Question: `What share of visits are with the patient's PCP?`
   - SQL:
     ```sql
     SELECT MEASURE(`Total Standard Visits`) AS total_standard_visits,
            MEASURE(`PCP Matched Visits`)     AS pcp_matched_visits,
            MEASURE(`PCP Continuity Ratio`)   AS pcp_continuity_ratio
     FROM {{CATALOG}}.{{SCHEMA}}.pcp_continuity_metrics
     GROUP BY ALL
     ```

   **Benchmark 3 — "overall continuity rate"** *(same expected SQL as Benchmark 2)*
   - Question: `What is the overall PCP continuity rate across all standard visits?`
   - SQL:
     ```sql
     SELECT MEASURE(`Total Standard Visits`) AS total_standard_visits,
            MEASURE(`PCP Matched Visits`)     AS pcp_matched_visits,
            MEASURE(`PCP Continuity Ratio`)   AS pcp_continuity_ratio
     FROM {{CATALOG}}.{{SCHEMA}}.pcp_continuity_metrics
     GROUP BY ALL
     ```

3. **Run** the benchmarks. Each row comes back with an **assessment**:
   - **Good** — Genie's generated SQL produced the same result as your expected SQL.
   - **Bad** — it differs; the row shows a **failure analysis** and a **SQL diff** — Genie's *Model output SQL* next to your *Ground truth SQL* — so you can see exactly what went wrong (a dropped filter, extra columns, wrong grain).

### Monitor — curate from real usage

The **Monitor** tab turns real usage into improvements. It logs the **actual questions** analysts asked this agent, the SQL Genie generated for each, and any feedback left on them.

**Walk it:**

1. Open your Genie agent and select **Monitor** at the top.
2. You'll see the log of questions people have asked — each row shows the **question**, the **SQL Genie generated**, and the answer, plus any 👍 / 👎 / *Fix it* feedback.
3. Scan for the misses — 👎'd answers, or rows where the generated SQL is wrong. Each miss is a curation task: promote it into the right governed context —
   - an everyday word Genie didn't map → add a **synonym**
   - a metric it recomputed by hand → point it at the **metric view** (or add a **SQL expression**)
   - a question it should route to the function but didn't → add an **example query** (the lever from earlier in Part 7)
   - missing governed logic → register the **trusted asset** + a routing instruction
4. Close the loop with the **Benchmark** tab: add the fixed question as a benchmark row and **Run**, so the fix is proven and stays fixed.

> **Seed it before you demo.** The **Monitor** tab only fills from real asks, so it's empty on a brand-new agent. Ask the agent a few questions first — the two rate phrasings and the provider question from above — so the tab has content to show. Ask the naive *"what share of visits are with the patient's PCP?"* (the **65.5%** miss) and 👎 it: that's the exact row you then fix and re-benchmark, live.

> **The loop:** **Monitor** tells you *what to fix* → a trusted asset / instruction / example query *fixes it* → the **Benchmark** *proves it stayed fixed*. That's how a Genie Agent matures from "demo" to "trusted."

## Part 8 - Author your own metric view & function *(extra exercise, if time)*

You've *used* the governed assets in Parts 5–7 — now **build them yourself** to get hands-on with authoring metric views and SQL functions. You'll re-create the two you saw: the `pcp_continuity_metrics` metric view and the `pcp_continuity_by_provider` function. Build them in **`{{CATALOG}}.analyst101_<you>`** (your own schema), reading the shared **synthetic** base data you have SELECT on. Same steps, same syntax you'll use to stand up metric views and functions on your **own** data back home — this is the reps, on safe data.

> **Don't have your own schema yet?** If you skipped Part 0, create it first — left nav → **Catalog** → click the catalog **`{{CATALOG}}`** → **Create schema** (top-right) → name it **`analyst101_<you>`** (e.g. `analyst101_jsmith`), leave the default storage location, **Create**. *(If **Create schema** is greyed out, tell your instructor — the workshop group needs `CREATE SCHEMA` on `{{CATALOG}}`.)*

**1 · The metric view — one governed definition.** A metric view's `source` is a single relation, so continuity sources the shared **`encounters_enriched`** convenience view (one row per encounter with `visit_type_id` and an `is_pcp_match` flag already computed; standard visits are `visit_type_id = 'OFFICE'`). Run this in a SQL editor:

```sql
CREATE OR REPLACE VIEW {{CATALOG}}.analyst101_<you>.pcp_continuity_metrics
(`Facility`, `Facility Code`, `Region`, `Encounter Month`,
 `Total Standard Visits`, `PCP Matched Visits`, `PCP Continuity Ratio`)
COMMENT 'Governed PCP continuity metrics over STANDARD visits only. Define the ratio once.'
WITH METRICS
LANGUAGE YAML
AS $yaml$
version: 0.1
source: {{CATALOG}}.{{SCHEMA}}.encounters_enriched
filter: visit_type_id = 'OFFICE'
dimensions:
  - name: Facility
    expr: facility_name
  - name: Facility Code
    expr: facility_id
  - name: Region
    expr: region
  - name: Encounter Month
    expr: date_trunc('MONTH', admit_date)
measures:
  - name: Total Standard Visits
    expr: COUNT(1)
  - name: PCP Matched Visits
    expr: COUNT_IF(is_pcp_match)
  - name: PCP Continuity Ratio
    expr: TRY_DIVIDE(COUNT_IF(is_pcp_match), COUNT(1))
$yaml$;
```

Query it like the shared one — measures via `MEASURE()`, grouped by a dimension:

```sql
SELECT `Facility`, ROUND(MEASURE(`PCP Continuity Ratio`)*100,1) AS continuity_pct
FROM {{CATALOG}}.analyst101_<you>.pcp_continuity_metrics
GROUP BY `Facility` ORDER BY continuity_pct DESC;
```

*(Prefer the UI? **Catalog Explorer → Create → Metric view** offers AI-assisted authoring over the same YAML.)*

**2 · The `pcp_continuity_by_provider` function — the provider grain the metric view can't do.** A table function, self-contained (it joins the base tables in its body), parameterized by a date window:

```sql
CREATE OR REPLACE FUNCTION {{CATALOG}}.analyst101_<you>.pcp_continuity_by_provider(
  p_start STRING DEFAULT '2023-01-01',
  p_end   STRING DEFAULT '2025-12-31')
RETURNS TABLE (provider_name STRING, standard_visits BIGINT, matched_visits BIGINT, continuity_ratio DOUBLE)
COMMENT 'PCP continuity ratio per attending provider over standard visits in the date window.'
RETURN
  SELECT pr.provider_name,
         count(*) AS standard_visits,
         count_if(e.provider_id = pt.assigned_pcp_id) AS matched_visits,
         try_divide(count_if(e.provider_id = pt.assigned_pcp_id), count(*)) AS continuity_ratio
  FROM {{CATALOG}}.{{SCHEMA}}.fact_encounters e
  JOIN {{CATALOG}}.{{SCHEMA}}.dim_patient    pt ON e.patient_id    = pt.patient_id
  JOIN {{CATALOG}}.{{SCHEMA}}.dim_provider   pr ON e.provider_id   = pr.provider_id
  WHERE e.visit_type_id = 'OFFICE' AND e.admit_date BETWEEN to_date(p_start) AND to_date(p_end)
  GROUP BY pr.provider_name;
```

Call it (parameters have defaults, so `()` works):

```sql
SELECT provider_name, standard_visits, ROUND(continuity_ratio*100,1) AS continuity_pct
FROM {{CATALOG}}.analyst101_<you>.pcp_continuity_by_provider()
WHERE standard_visits >= 200 ORDER BY continuity_ratio DESC;
```

Grant `EXECUTE` to your Genie users, register these as trusted assets, and add an example query so Genie calls the function (Part 5's note) — and you've rebuilt the whole confidence stack on your own. *(The full reference DDL, including the `encounters_enriched` view, is in `advanced_module/continuity_assets.sql`.)*

---

# Capstone (take-home) — apply this to your own data

This is your **leave-behind**. The workshop used synthetic data so you could learn the moves safely; the capstone is where you point those same moves at **your own business data**. Use it back at your desk — pick a real question your team asks and build the answer here: a dashboard, a Genie Agent, or a governed metric.

**Start by thinking about your data:**
- What are your core **fact** and **dimension** tables (the things you count, and the things you slice by)?
- What's the one **metric** whose definition people argue about? That's your first governed metric view.
- Which **Tableau dashboard** would you most want to rebuild — and what would "better" look like?
- What's a question people ask in Slack/email that a **Genie Agent** on your data could just answer?

**Scenario ideas — pick one, or bring your own (all on *your* data):**

| Scenario | What it practices | On your data, think about… |
|---|---|---|
| A team / entity scorecard | aggregation, ranking, thresholds | your KPIs by rep, store, product, or region — rank them and threshold the ones that matter |
| A deep-dive on one segment | filtering, trend over time | pick one product line, customer segment, or cohort and trend its key measures |
| Two measures against each other | scatter, correlation | cost vs. outcome, spend vs. revenue, effort vs. result — one point per entity |
| A categorical mix | stacked bar, share-of | your mix by channel, category, or segment across a dimension |
| Genie-first exploration | NL querying → save to dashboard | ask your governed data plain-language questions, then pin the good answers |
| A governed metric | metric view + trusted asset | define your most-argued-about metric **once**, so every dashboard and Genie answer matches |
| Rebuild a Tableau dashboard | direct comparison | recreate one you know well; note what's easier and what's missing |

**Techniques to work in (whatever your scenario):**

- A filter and cross-filtering between two widgets.
- A drill-down hierarchy.
- A Genie question with the SQL revealed.
- A governed **metric view** for your headline number (the Part 8 pattern, on your data).

**Before you leave, jot down** your first move back home: the dashboard or Genie Agent you'll build, the tables it needs, and the one metric worth governing first.
