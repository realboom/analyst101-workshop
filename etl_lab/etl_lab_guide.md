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

## Step 1 · Create your schema and a Volume (in Catalog Explorer)

You'll do this in the **Catalog** UI — no code — so you get a feel for how Unity Catalog is
organized. Everything you build lives in **your own** schema, which you'll own.

**1.1 · Create your schema**

1. In the left nav, click **Catalog**.
2. Find and click the catalog **`{{CATALOG}}`**.
3. Click **Create schema** (top-right of the catalog page).
4. Name it **`analyst101_<you>`** (use your own name, e.g. `analyst101_jchen`), leave the storage
   location as the default, and click **Create**.

> If **Create schema** is greyed out or you get a permission error, tell your instructor — the
> workshop group needs `CREATE SCHEMA` on `{{CATALOG}}`.

**1.2 · Create a `landing` volume**

1. Open your new schema **`{{CATALOG}}.analyst101_<you>`**.
2. Click **Create → Volume** (top-right).
3. Name it **`landing`**, leave it a **Managed volume**, and click **Create**.

> A **volume** is the governed home for **files** (CSVs, images, PDFs) — it's where your raw file
> lands before it becomes a table. Creating one yourself once is worth doing so you know what it is.

## Step 2 · Upload the raw file

1. Open your new **`landing`** volume.
2. Click **Upload to this volume** and choose the **`facilities_raw.<profile>.csv`** file for
   your workshop (e.g. `facilities_raw.pediatric.csv`) — your instructor will share it, or
   download it from the workshop repo.
3. You'll see it listed. Peek at it — notice it's *messy on purpose*: extra spaces, `State`
   spelled every which way (full name / code / different case), inconsistent `Type`
   capitalization, two rows with a **blank Region**, a **duplicate** facility row, and a trailing
   empty line. This is what real source extracts look like. Our job is to fix it.

## Step 3 · Open Lakeflow Designer (Visual Data Prep) and start a build

1. Left nav → **Data Engineering → Visual Data Prep**. *(This is the Lakeflow Designer visual, no-code ETL builder — under Data Engineering you'll see **Runs**, **Data Ingestion**, and **Visual Data Prep**; pick the last one.)*
2. Click **Create** (or **New**) to start a pipeline; name it **`facilities_medallion`**.
3. You land on a **start screen** with a **Genie prompt box** and tiles like **Select a source**,
   **Upload a file**, **Load a sample**, and **try a Genie code prompt**. From here there are **two
   ways to build** — pick one in Step 4:
   - **Option A — prompt Genie** to build the pipeline for you (the fast, AI-assisted way), or
   - **Option B — build it by hand**, adding operators one at a time.

## Step 4 · Build bronze → silver → gold — two ways

You're turning the messy file into a clean 12-row `dim_facility`. Do it **either** way below. The
transformations are the same; the difference is whether **Genie writes the steps for you** (Option A)
or **you add them yourself** (Option B).

> **Bronze → silver → gold here are stages in one pipeline, not three separate tables.** Bronze is the
> raw read, silver is the cleaning/conforming, and the only table you save is the **gold**
> `dim_facility` — the business-ready dimension your dashboards and Genie read.

### Option A · Prompt Genie to build it (AI-assisted) — the fast way

1. On the start screen, choose **Select a source** and point at your `landing` volume's
   **`facilities_raw.<profile>.csv`** so Genie has the data in front of it.
2. In the **Genie prompt box**, describe the outcome in plain English and let Genie generate the
   transformation steps. Paste something like:
   > Clean this facilities CSV into a table called **dim_facility**. Trim whitespace on all text
   > columns. Standardize **State** to a 2-letter US state code (e.g. Utah → UT). Proper-case **Type**.
   > Drop rows where **Facility ID** is blank. Remove duplicate rows by **Facility ID**. Fill any
   > blank **Region** from another facility in the same **City**. Rename columns to snake_case:
   > facility_id, facility_name, facility_type, city, state, region.
3. **Review the steps Genie generated** — each shows a live preview. Tweak anything that's off
   (this is the point: you can inspect and edit every step).
4. Set the output to a **Table** named **`dim_facility`** in **`{{CATALOG}}.analyst101_<you>`**,
   with mode **Create/replace**, then **Run**. *(Output type **Table** — a materialized view isn't
   needed here and may not be available in every workspace/region. Mode **Create/replace** rebuilds the
   full table each run; merge/append are for incremental loads, not this full-file build.)*

### Option B · Build it by hand (operator by operator) — the manual way

**Bronze — bring the raw file in exactly as-is**

1. Click **Select a source** and point at `{{CATALOG}}.analyst101_<you>.landing` →
   **`facilities_raw.<profile>.csv`** (Designer auto-detects CSV).
2. Confirm it parsed into columns (`Facility ID`, `Facility Name`, `Type`, `City`, `State`,
   `Region`). Leave everything raw — **no cleaning yet**. You should see ~13 rows (the dupe and the
   blank line are still here — expected). *Bronze is the source, faithfully — the receipt of what arrived.*

**Silver — clean and conform** (add transform steps one at a time; each shows a live preview):

1. **Trim whitespace** on `Facility Name`, `Type`, `City`, `State`, `Region`.
2. **Standardize `State` to a 2-letter code** — uppercase `State`, then map full names to codes
   (e.g. `UTAH→UT`, `CALIFORNIA→CA`); leave good codes alone.
3. **Proper-case `Type`** — title-case so `pediatric clinic` / `PEDIATRIC CLINIC` / `Pediatric Clinic`
   all become **`Pediatric Clinic`**.
4. **Drop empty rows** — filter out rows where `Facility ID` is null/blank (kills the trailing line).
5. **De-duplicate** on **`Facility ID`** (standardize *first*, so the duplicate is a true dupe by now).

→ **12 clean, conformed rows** — but two still have a blank `Region`.

**Gold — make it business-ready `dim_facility`**

1. **Fill the missing `Region`** from a same-`City` sibling: a **window/group** step taking
   `MAX(Region)` (or first non-null) **partitioned by `City`**, applied where `Region` is blank. **No more blanks.**
2. **Rename to snake_case**: `Facility ID→facility_id`, `Facility Name→facility_name`,
   `Type→facility_type`, `City→city`, `State→state`, `Region→region`.
3. **Set the output** to a **Table** named **`dim_facility`** in **`{{CATALOG}}.analyst101_<you>`**, mode **Create/replace**, then **Run**. *(Table type + Create/replace rebuilds the full 12-row dim each run; merge/append are for incremental loads, not this full-file build.)*

## Step 5 · Verify + the governance payoff

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
