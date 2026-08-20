# ETL Lab — From a Raw File to a Governed Table

**Goal:** take a messy CSV a source system handed you and turn it into a clean, governed
`dim_facility` table — using **no code**, in the Databricks **Lakeflow Designer** visual ETL
builder. Along the way you'll meet the building blocks every Databricks project uses: a
**catalog**, a **schema**, a **volume**, and the **medallion (bronze → silver → gold)** pattern.

> You'll build everything into **your own schema**, which you create in Step 1, so you can click
> freely without stepping on anyone else. Pick a schema name based on your own name —
> **`{{CATALOG}}.analyst101_<your-name>`** (e.g. `analyst101_jchen`). Everywhere below that says
> `analyst101_<you>`, use yours.

---

## The concepts (2 minutes, then we click)

- **Catalog → Schema → Table** is just Databricks' three-level namespace, like
  *database server → database → table* elsewhere. Everything lives in **Unity Catalog**, which
  governs who can see and do what.
- **Volume** = a governed folder for **files** (CSVs, images, PDFs) that lives under a schema.
  It's where raw files land before they become tables.
- **Medallion architecture** is the industry-standard way to refine data in layers:
  - **Bronze** = raw, as-ingested. A faithful copy of the source, warts and all.
  - **Silver** = cleaned and conformed. Trimmed, typed, standardized, de-duplicated.
  - **Gold** = business-ready. The table your dashboards and Genie actually use.

Today: **upload a raw facilities file → bronze → silver → gold `dim_facility`.**

---

## Step 1 · Create your schema and a Volume for the raw file

First make **your own** schema — this is your personal workspace for the lab and you'll own everything in it.

1. Open a **SQL editor** (left nav → **SQL Editor**) and run, using your own name:
   ```sql
   CREATE SCHEMA IF NOT EXISTS {{CATALOG}}.analyst101_<you>;
   ```
   (If this errors with a permissions message, tell your instructor — the workshop group needs
   `CREATE SCHEMA` on `{{CATALOG}}`.)
2. In the left nav, click **Catalog**, then expand catalog **`{{CATALOG}}`** → your new schema
   **`analyst101_<you>`**.
3. Click **Create → Volume**. Name it **`landing`**, leave it a **Managed volume**, **Create**.

> A volume is the right home for a file. You *could* drag a file straight onto the Designer
> canvas (it uploads to a volume for you), but creating one yourself is worth doing once so you
> know what a volume is.

## Step 2 · Upload the raw file

1. Open your new **`landing`** volume.
2. Click **Upload to this volume** and choose the **`facilities_raw.<profile>.csv`** file for
   your workshop (e.g. `facilities_raw.pediatric.csv`) — your instructor will share it, or
   download it from the workshop repo.
3. You'll see it listed. Peek at it — notice it's *messy on purpose*: extra spaces, `State`
   spelled every which way (full name / code / different case), inconsistent `Type`
   capitalization, two rows with a **blank Region**, a **duplicate** facility row, and a trailing
   empty line. This is what real source extracts look like. Our job is to fix it.

## Step 3 · Open Lakeflow Designer and start a build

1. Left nav → **Data Engineering → Lakeflow** (or search **"Designer"** in the top search bar).
2. Click **New → Visual data prep**. Name it **`facilities_medallion`**.
3. You get a blank canvas. You build a pipeline by adding **operators** and connecting them.

## Step 4 · Bronze — bring the raw file in exactly as-is

1. Click **Select source operator** (or **+ → Source**).
2. Choose **Browse** and navigate to `{{CATALOG}}.analyst101_<you>.landing` → your
   **`facilities_raw.<profile>.csv`** (or **Ingest a folder/volume** and point at the `landing`
   volume — Designer auto-detects CSV).
3. In the source pane, confirm it parsed into columns (`Facility ID`, `Facility Name`, `Type`,
   `City`, `State`, `Region`). Leave everything raw — **no cleaning yet**. Click **Apply**.
4. This is your **bronze** layer: the source, faithfully. You should see ~13 rows (the dupe and
   the blank line are still here — that's expected).

> **Talking point:** bronze is deliberately un-touched. If a question comes up later about what
> the source actually sent, bronze is the receipt.

## Step 5 · Silver — clean and conform

Add transform operators one at a time (each shows a live preview so you see the effect):

1. **Trim whitespace** — add a **Transform / Clean** step and trim leading/trailing spaces on
   `Facility Name`, `Type`, `City`, `State`, `Region`. (Watch the padded names snap into place.)
2. **Standardize `State` to a 2-letter code** — add a **derived / case** expression: uppercase
   `State`, then map any full state name to its code (e.g. `UTAH→UT`, `CALIFORNIA→CA`) using a
   standard US-state lookup; leave already-good codes. Now every row is a clean 2-letter code.
3. **Proper-case `Type`** — apply title-case so e.g. `pediatric clinic`, `PEDIATRIC CLINIC`, and
   `Pediatric Clinic` all become one value: **`Pediatric Clinic`**.
4. **Drop empty rows** — add a **Filter** that removes rows where `Facility ID` is null/blank
   (kills the trailing empty line).
5. **De-duplicate** — add a **Remove duplicates / Deduplicate** step keyed on **`Facility ID`**.
   The duplicated facility row collapses to one. (Notice we standardized *first*, so the duplicate
   is a true duplicate by the time we dedupe.)

You now have a **silver** result: **12 clean, conformed rows** — but two of them still have a
blank `Region`.

## Step 6 · Gold — make it business-ready `dim_facility`

1. **Fill the missing `Region`** — the two blank-region rows each share a **City** with another
   facility that *does* have a region. Fill the blank from that same-city sibling: add a
   **window / group** step that takes `MAX(Region)` (or first non-null) **partitioned by `City`**,
   and use it where `Region` is blank. Data fills the gap — no hand-typed lookup needed.
   **No more blanks.**
2. **Rename to the final schema** (snake_case) so it matches how tables are named here:
   `Facility ID→facility_id`, `Facility Name→facility_name`, `Type→facility_type`,
   `City→city`, `State→state`, `Region→region`.
3. **Set the output / destination**: write to a table named **`dim_facility`** in
   **`{{CATALOG}}.analyst101_<you>`**. Choose **Materialized** (a managed table).
4. Click **Run** (or **Publish + Run**). Designer generates the pipeline and runs it.

## Step 7 · Verify + the governance payoff

1. Back in **Catalog**, open `{{CATALOG}}.analyst101_<you>.dim_facility`. Confirm **12 rows**,
   clean `state` codes, proper-cased `facility_type`, and **no blank regions**.
2. Open the **Lineage** tab — you'll see the graph: `facilities_raw.<profile>.csv` (volume) → bronze →
   silver → **`dim_facility`**. You didn't write a line of code, but you got a governed,
   fully-lineaged pipeline you could schedule to run every night.
3. *(Optional, if you want the full dimension treatment)* add a primary key + comments:
   ```sql
   ALTER TABLE {{CATALOG}}.analyst101_<you>.dim_facility ALTER COLUMN facility_id SET NOT NULL;
   ALTER TABLE {{CATALOG}}.analyst101_<you>.dim_facility ADD CONSTRAINT pk_dim_facility PRIMARY KEY (facility_id);
   COMMENT ON TABLE {{CATALOG}}.analyst101_<you>.dim_facility IS 'Hospitals and clinics with type, city, state, region. One row per facility.';
   ```

**What you just did:** turned a raw file into a governed, documented, business-ready table with
a repeatable, no-code pipeline. This `dim_facility` is exactly the kind of table the AI/BI
dashboards and Genie read in the next part of the workshop.
