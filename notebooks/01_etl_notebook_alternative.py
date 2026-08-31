# Databricks notebook source
# /// script
# [tool.databricks.environment]
# environment_version = "5"
# ///
# MAGIC %md
# MAGIC # Analyst 101 — ETL the code way (notebook alternative to Visual Data Prep)
# MAGIC
# MAGIC The **same** raw-file → governed `dim_facility` lab as **Part 0**, but done in a notebook instead of
# MAGIC the no-code **Lakeflow Designer / Visual Data Prep** builder. Use this when the session is short on
# MAGIC time, or to show analysts who prefer code what the visual pipeline does under the hood — the
# MAGIC transformations and the 12-row result are identical.
# MAGIC
# MAGIC **Prereqs (Part 0, Steps 1–2 — same for both paths):** you've created your own schema
# MAGIC `{{CATALOG}}.analyst101_<you>`, created a **`landing`** volume in it, and uploaded
# MAGIC `facilities_raw.<profile>.csv` into `landing`. All data is **synthetic — no PHI**.
# MAGIC
# MAGIC **Three cells:** (1) read + **explore** the CSV · (2) query it with **`%sql`** · (3) clean it with
# MAGIC **Spark SQL** into `dim_facility`. Attach to **serverless**, fill the widgets, run top to bottom.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Setup · point at your uploaded file
# MAGIC Fill the three widgets at the top (set **schema** to *your* schema and **profile** to the CSV you
# MAGIC uploaded), then run this cell.

# COMMAND ----------

dbutils.widgets.text("catalog", "acme_analyst101", "1. Catalog")
dbutils.widgets.text("schema", "analyst101_yourname", "2. Your schema (analyst101_<you>)")
dbutils.widgets.dropdown("profile", "pediatric", ["pediatric", "adult"], "3. Data profile (which CSV you uploaded)")

CATALOG = dbutils.widgets.get("catalog").strip()
SCHEMA  = dbutils.widgets.get("schema").strip()
PROFILE = dbutils.widgets.get("profile").strip()

csv_path = f"/Volumes/{CATALOG}/{SCHEMA}/landing/facilities_raw.{PROFILE}.csv"
target   = f"{CATALOG}.{SCHEMA}.dim_facility"
print("Reading CSV from :", csv_path)
print("Will write table :", target)

# COMMAND ----------

# DBTITLE 1,Cell 4
# MAGIC %md
# MAGIC ## Cell 1 of 3 · Explore the raw CSV with `read_files()`
# MAGIC Use the `read_files()` SQL function to scan the raw file directly — no Python needed. Eyeball the
# MAGIC mess: padded text, `State` spelled every which way, inconsistent `Type` case, blank `Region`s, and a
# MAGIC duplicate row. This is the **bronze** (raw, as-ingested) layer.

# COMMAND ----------

# DBTITLE 1,Cell 5
# MAGIC %sql
# MAGIC -- Explore the raw CSV directly — scan for padded text, inconsistent State/Type, blank Regions, dupes
# MAGIC SELECT *
# MAGIC FROM read_files(
# MAGIC   '/Volumes/' || :catalog || '/' || :schema || '/landing/facilities_raw.' || :profile || '.csv',
# MAGIC   format => 'csv',
# MAGIC   header => 'true'
# MAGIC )
# MAGIC
# MAGIC -- SELECT *
# MAGIC -- FROM read_files(
# MAGIC --   '/Volumes/' || :catalog || '/' || :schema || '/landing/facilities_raw.' || :profile || '.csv',
# MAGIC --   format => 'csv',
# MAGIC --   header => 'true',
# MAGIC --   schema => 'facility_id INT, facility_name STRING, region STRING, beds INT, opened_date DATE'
# MAGIC -- )

# COMMAND ----------

# DBTITLE 1,Cell 6
# MAGIC %md
# MAGIC ## Cell 2 of 3 · Create the temp view for downstream ETL
# MAGIC Read the same file into a Spark DataFrame and register it as `facilities_raw` — the SQL-based
# MAGIC cleaning step below queries this view.

# COMMAND ----------

# DBTITLE 1,Create temp view for ETL
raw = (spark.read
       .option("header", True)
       .option("inferSchema", True)
       .csv(csv_path))

# Register a temp view so the cleaning SQL below can query it
raw.createOrReplaceTempView("facilities_raw")
print(f"✅ Temp view 'facilities_raw' created — {raw.count()} rows ready for ETL")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Cell 3 of 3 · Clean it with Spark SQL → `dim_facility`
# MAGIC One Spark SQL statement does the **silver** (trim, standardize `State` to a 2-letter code, proper-case
# MAGIC `Type`, drop blank IDs) and **gold** (fill blank `Region` from a same-`City` sibling, de-duplicate,
# MAGIC snake_case) work — the same result as the Visual Data Prep pipeline: **12 clean rows**. Then write it
# MAGIC as your governed `dim_facility`.

# COMMAND ----------

clean = spark.sql("""
WITH silver AS (                              -- trim, standardize, drop blank IDs
  SELECT
    trim(`Facility ID`)                                     AS facility_id,
    trim(`Facility Name`)                                   AS facility_name,
    initcap(trim(Type))                                     AS facility_type,   -- 'pediatric hospital' -> 'Pediatric Hospital'
    trim(City)                                              AS city,
    CASE upper(trim(State))                                                    -- full names -> 2-letter code
      WHEN 'COLORADO' THEN 'CO'
      WHEN 'MISSOURI' THEN 'MO'
      WHEN 'ARIZONA'  THEN 'AZ'
      ELSE upper(trim(State))                                                  -- 'wa'/'WA'/'CO ' -> 'WA'/'CO'
    END                                                     AS state,
    nullif(trim(Region), '')                                AS region
  FROM facilities_raw
  WHERE `Facility ID` IS NOT NULL AND trim(`Facility ID`) <> ''
),
gold AS (                                     -- fill blank Region from a same-City sibling, then de-duplicate
  SELECT DISTINCT
    facility_id, facility_name, facility_type, city, state,
    coalesce(region, max(region) OVER (PARTITION BY city)) AS region
  FROM silver
)
SELECT * FROM gold ORDER BY facility_id
""")

print(f"Clean row count: {clean.count()}")   # 12
display(clean)

# write the governed gold table (same object the Visual Data Prep path produces)
clean.write.mode("overwrite").saveAsTable(target)
print(f"✅ wrote {target}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## You're back on the Part 0 path
# MAGIC You now have the same governed `dim_facility` the visual builder produces. Continue with:
# MAGIC - **Part 0, Step 5 — Verify:** open `{{CATALOG}}.analyst101_<you>.dim_facility` in Catalog (12 rows,
# MAGIC   clean states, proper-cased types, no blank regions) and check the **Lineage** tab.
# MAGIC - **Part 0, Step 6 — Make it Genie-ready:** run the `COMMENT ON` / `PRIMARY KEY` block so the table is
# MAGIC   documented for Genie and the AI/BI Assistant — this matters for **Part 4**.
# MAGIC
# MAGIC > **Note on lineage:** UC lineage tracks *persisted objects*, so you'll see `facilities_raw.<profile>.csv`
# MAGIC > (volume) → `dim_facility` (table). The bronze → silver → gold steps here live **inside this notebook's
# MAGIC > SQL**, just as the visual path keeps them inside the pipeline's operator graph.