# Attendee Workbook - {{CLIENT_NAME}} Analyst 101 Workshop (AI/BI half)

Welcome. This is the **AI/BI half** of the workshop — building dashboards and asking questions in
plain language with Genie, on a shared synthetic {{INDUSTRY_FLAVOR}} dataset. It picks up right
after the **Foundations + ETL lab** (`etl_lab/etl_lab_guide.md`), where you built a governed
`dim_facility` table from a raw file. Now we use tables like it. Follow along on your own screen,
and ask questions any time.

> **Part 0 — did you do the ETL lab first?** If not, that's where you create a volume, upload a
> file, and build a bronze→silver→gold pipeline in Lakeflow Designer. See
> `etl_lab/etl_lab_guide.md`. This workbook assumes you've seen it.

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
| `dim_procedure` | Procedure codes (incl. 27447 total knee replacement). |
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

# DAY 1

> **Single-session Analyst 101?** Follow `agenda.md`: you'll do **Parts 1–3** below plus the **Genie**
> segment. The "Day 1 / Day 2" split here is the fuller two-day layout — use it if you have the time.

> **Capabilities we will cover today:** rich interactive visuals (combo, heatmap, map, pivot, scorecard), calculated dimensions and measures, parameterized widgets, cross-filtering, drilling, forecasting and AI functions, multipage reporting, and Ask Genie from a published dashboard. The companion one-pager has a quick reference for each.

## Part 1 - The dataset is your analytics engine (window functions, ranking, period-over-period)

The key idea: a dataset is **full Databricks SQL**. The things you do with table calcs, LOD expressions, and rank in Tableau are just window functions here, defined once in the dataset and reused by every widget. We'll go straight to the kind of analysis you actually do.

**Step 1 · Create the dashboard.**

- In the left nav, click **Dashboards**, then **Create dashboard**. Name it "My {{CLIENT_NAME}} Workshop".
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
       encounters - LAG(encounters,1)  OVER (ORDER BY month) AS mom_change,
       ROUND(100.0*(encounters - LAG(encounters,12) OVER (ORDER BY month))
             / LAG(encounters,12) OVER (ORDER BY month), 1) AS yoy_pct,
       ROUND(AVG(encounters) OVER (ORDER BY month ROWS BETWEEN 2 PRECEDING AND CURRENT ROW),0)
             AS rolling_3mo,
       ROUND(readmit_rate,1) AS readmit_rate_pct
FROM m
```

- **Canvas** tab → **Add a visualization**. **Dataset:** `Outcome trend`. **Visualization:** Combo (bar + line).
- **X axis:** `month`.
- **Bars (left/primary Y):** `encounters`.
- **Line (right/secondary Y):** `rolling_3mo`.
- **Optional second line:** `yoy_pct` (it's a percent, so keep it on the secondary axis or put it in its own small chart).
- **Sort:** X axis ascending by `month`.

**Step 5 · Add calculated fields (no code).** You don't have to do everything in SQL.

- On the `Provider performance` dataset (or any dataset), in the **Data** tab, add a **calculated measure** with a formula, for example a paid-to-charge ratio: `SUM(total_paid) / SUM(total_charges)`. (Use a dataset that carries `total_paid` and `total_charges` if you want this one, e.g. build it on `fact_encounters`.)
- Add a **calculated dimension** that bins a field, for example an age band: `CASE WHEN patient_age < 40 THEN '<40' WHEN patient_age < 65 THEN '40-64' ELSE '65+' END`.
- Use them in any visual (as a column, axis, or color). They recompute automatically as filters change.

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

---

## Part 4 - Publish your dashboard and turn it into a Genie space

Now the fun part. You'll publish the dashboard you just built, spin up a Genie space directly from it, give it a few instructions, and ask questions in plain language.

**Step 1 · Publish.**

- Click **Publish** (top right) to publish your dashboard.

**Step 2 · Create a Genie space from the dashboard.**

- From your published dashboard, use the **Genie** / "Create Genie space" control on the dashboard. This builds a Genie space on your dashboard's data.

**Step 3 · Add instructions.**

- Open the new Genie space and find the **Instructions** area. Paste in the block below (your instructor also shares it). Save.

Instructions block to paste:
```
This Genie space answers questions about synthetic hospital encounters. There is no PHI.

Data model:
- fact_encounters is the central fact table, one row per patient encounter.
- Join to dim_provider on provider_id, dim_facility on facility_id,
  dim_diagnosis on primary_icd10_code = icd10_code, and dim_procedure on
  primary_procedure_code = procedure_code. (These foreign keys are already defined.)

Metric definitions (express all rates as a percentage from 0 to 100):
- Readmission rate = AVG(readmitted_30d) * 100
- Mortality rate = AVG(mortality_flag) * 100
- Complication rate = AVG(complication_flag) * 100
- Average length of stay = AVG(length_of_stay_days), in days

Conventions:
- When ranking providers or facilities by a rate, only include those with at least
  200 encounters unless the user asks otherwise.
- Show plain-language names in results (provider_name, facility_name, region,
  clinical_category, procedure_description), not the id columns.
- "knee replacement" means primary_procedure_code = '27447'.
- Round rates to one decimal place and currency to whole dollars.
```

**Step 4 · Ask a few questions.** Try these, then your own:

- "How many encounters were there in 2024 by region?"
- "Which providers have the highest 30-day readmission rate, with at least 200 encounters?"
- "What is the average length of stay for a knee replacement?"

**Step 5 · Show the SQL.** On any answer, click **Show generated code** to see the Databricks SQL Genie wrote.

> **Why this is so quick:** the dataset is fully documented (every column has a description and the table relationships are defined), so Genie already knows how to join the tables. You only add a few instructions on top.
>
> **For the SQL folks:** Genie writes Databricks SQL, so it's a fast way to see the correct syntax and functions when you translate from what you write today. Copy it and build on it.
>
> **Trust:** every answer shows its SQL, Genie only sees tables you've been granted, and you can give feedback (Yes / Fix it / Request review). It's a fast first draft, not a black box.

---

## End of Day 1
Jot down, for the wrap-up:

- One thing that was faster or easier than Tableau.
- One thing you'd miss from Tableau.
- **Your Day-2 scenario:** a question you want answered, or a report/dashboard you'd like to recreate. If you have an existing Tableau dashboard in mind, bring it.

---

# DAY 2 - Build your own scenario

Pick a scenario (yours, or one below) and build it. Instructors will float to help. Aim for something you can show the group in a few minutes. Same loop as Day 1: define a dataset on the Data tab, then add visualizations on the Canvas (set Dataset, Visualization type, and fields).

**Starter scenarios:**

| Scenario | Good for practicing | Starter query (adapt freely) |
|---|---|---|
| Provider outcomes scorecard | aggregation, ranking, thresholds | `SELECT p.provider_name, COUNT(*) enc, ROUND(100.0*SUM(e.complication_flag)/COUNT(*),1) comp_rate FROM {{CATALOG}}.{{SCHEMA}}.fact_encounters e JOIN {{CATALOG}}.{{SCHEMA}}.dim_provider p USING(provider_id) GROUP BY 1 HAVING enc>200 ORDER BY comp_rate DESC` |
| Knee replacement deep-dive | filtering to a procedure, trend | filter `primary_procedure_code = '27447'`; trend LOS and readmit over time; split by facility |
| Cost vs. outcome | two measures, scatter | `SELECT f.facility_name, AVG(e.total_paid) avg_paid, 100.0*SUM(e.readmitted_30d)/COUNT(*) readmit_rate FROM {{CATALOG}}.{{SCHEMA}}.fact_encounters e JOIN {{CATALOG}}.{{SCHEMA}}.dim_facility f USING(facility_id) GROUP BY 1` |
| Payer mix by region | stacked bar, categorical split | `SELECT f.region, e.payer_type, COUNT(*) enc FROM {{CATALOG}}.{{SCHEMA}}.fact_encounters e JOIN {{CATALOG}}.{{SCHEMA}}.dim_facility f USING(facility_id) GROUP BY 1,2` |
| Genie-first | NL querying, then save to dashboard | ask the Genie space, then add a good answer to a dashboard |
| Rebuild one of your Tableau dashboards | direct comparison | recreate a dashboard you know well and note what's easier and what's missing |

**As you build, try at least one of each:**

- A filter and cross-filtering between two widgets.
- A drill-down hierarchy.
- A question in Genie, with the SQL revealed.

**Share-out:** be ready to show what you built, what surprised you, and your honest read on where this fits versus Tableau.

**A scatter tip (for cost vs. outcome):** set the X axis to one measure (e.g. `avg_paid`), the Y axis to the other (e.g. `readmit_rate`), and the point label to `facility_name`.
