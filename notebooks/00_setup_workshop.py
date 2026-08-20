# Databricks notebook source
# MAGIC %md
# MAGIC # Analyst 101 — one-time workshop setup
# MAGIC
# MAGIC Run this **once per workspace** before the workshop to build the shared dataset, dashboard, and
# MAGIC Genie space. It's the "Step 0" the attendees never do — they only build their own `dim_facility`
# MAGIC in the ETL lab. All data is **synthetic — no PHI**.
# MAGIC
# MAGIC **Prerequisites:** this notebook lives inside the repo you added as a **Git folder**
# MAGIC (`Workspace → Create → Git folder → https://github.com/realboom/analyst101-workshop.git`).
# MAGIC Attach it to **serverless**. No CLI, no local tools, no tokens — the Databricks SDK is
# MAGIC auto-authenticated inside the notebook.
# MAGIC
# MAGIC **How to use:** run **Step 0a** to create the input widgets, fill them in at the top of the
# MAGIC notebook, then run **Step 0b** and **Steps 1–6 one at a time**, top to bottom, reading each
# MAGIC output before moving on.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 0a · Create the input widgets
# MAGIC Run this cell **once**. The eight input boxes appear at the **top of the notebook** — fill them
# MAGIC in there, then run Step 0b. (For RCH: profile `pediatric`, headline surgery `tonsillectomy` / `42820`.)

# COMMAND ----------

dbutils.widgets.text("catalog", "acme_analyst101", "1. Catalog (created if missing)")
dbutils.widgets.text("schema", "analyst101_shared", "2. Shared schema")
dbutils.widgets.dropdown("profile", "adult", ["adult", "pediatric"], "3. Data profile")
dbutils.widgets.text("client_name", "Acme Health", "4. Client display name")
dbutils.widgets.text("procedure_example", "knee replacement", "5. Headline surgery (demo example)")
dbutils.widgets.text("procedure_code", "27447", "6. Its procedure code")
dbutils.widgets.text("warehouse_id", "", "7. SQL warehouse id (blank = auto-pick serverless)")
dbutils.widgets.text("attendee_group", "analyst101_attendees", "8. Attendee group (for grants)")

print("Widgets created — scroll to the top of the notebook, fill them in, then run Step 0b.")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 0b · Read the inputs + connect
# MAGIC After filling the widgets at the top, run this to load them, connect via the SDK, and pick a warehouse.

# COMMAND ----------

CATALOG   = dbutils.widgets.get("catalog").strip()
SCHEMA    = dbutils.widgets.get("schema").strip()
PROFILE   = dbutils.widgets.get("profile").strip()
CLIENT    = dbutils.widgets.get("client_name").strip()
PROC_EX   = dbutils.widgets.get("procedure_example").strip()
PROC_CODE = dbutils.widgets.get("procedure_code").strip()
WAREHOUSE = dbutils.widgets.get("warehouse_id").strip()
GROUP     = dbutils.widgets.get("attendee_group").strip()

from databricks.sdk import WorkspaceClient
w = WorkspaceClient()

# auto-pick a serverless warehouse if none supplied
if not WAREHOUSE:
    whs = list(w.warehouses.list())
    serverless = [x for x in whs if getattr(x, "enable_serverless_compute", False)]
    pick = (serverless or whs)
    if not pick:
        raise Exception("No SQL warehouse found — create a serverless warehouse or set the warehouse_id widget.")
    WAREHOUSE = pick[0].id
    print(f"Auto-picked warehouse: {pick[0].name} ({WAREHOUSE})")

ME = w.current_user.me().user_name
PARENT = f"/Workspace/Users/{ME}"
FQ = lambda obj: f"{CATALOG}.{SCHEMA}.{obj}"

print(f"Catalog.Schema : {CATALOG}.{SCHEMA}")
print(f"Profile        : {PROFILE}   (headline surgery: {PROC_EX} = {PROC_CODE})")
print(f"Warehouse id   : {WAREHOUSE}")
print(f"Dashboards/Genie parent: {PARENT}")

# guardrail: the headline surgery must exist in the chosen profile
_known = {"adult": ("knee replacement", "27447"), "pediatric": ("tonsillectomy", "42820")}
_ex, _code = _known.get(PROFILE, (None, None))
if _code and PROC_CODE != _code:
    print(f"\n⚠️  Profile '{PROFILE}' does not contain procedure {PROC_CODE}. "
          f"For {PROFILE}, use {_ex} = {_code}, or the Genie surgery question will return nothing.")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 1 · Generate the star schema
# MAGIC Runs the widget-driven generator notebook. Creates the catalog + schema (if needed) and ~80k
# MAGIC encounters + dimensions, fully documented with PK/FKs. Takes a couple of minutes.

# COMMAND ----------

result = dbutils.notebook.run(
    "../data_generation/generate_workshop_data",
    3600,
    {"catalog": CATALOG, "schema": SCHEMA, "profile": PROFILE},
)
print("Generator finished:", result)
print("\nTables now in the schema:")
display(spark.sql(f"SHOW TABLES IN {CATALOG}.{SCHEMA}"))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 2 · Advanced module — metric view + 3 SQL functions
# MAGIC Reads `advanced_module/continuity_assets.sql`, fills the `{{CATALOG}}`/`{{SCHEMA}}` tokens
# MAGIC in-memory, and runs each statement. Creates `encounters_enriched`, the `pcp_continuity_metrics`
# MAGIC metric view, and the 3 trusted functions.

# COMMAND ----------

def split_sql(text):
    """Split a .sql file into statements. Strips -- line comments and splits on ';', but never
    inside a $$...$$ block or a '...' string (so semicolons in COMMENT text / YAML don't mis-split)."""
    lines = [ln for ln in text.splitlines() if not ln.strip().startswith("--")]
    text = "\n".join(lines)
    stmts, buf = [], []
    in_dollar = in_str = False
    i, n = 0, len(text)
    while i < n:
        if not in_str and text[i:i+2] == "$$":      # toggle $$ dollar-quote block
            in_dollar = not in_dollar
            buf.append("$$"); i += 2; continue
        c = text[i]
        if not in_dollar and c == "'":              # toggle single-quoted string ('' = escaped quote)
            if in_str and text[i+1:i+2] == "'":
                buf.append("''"); i += 2; continue
            in_str = not in_str
            buf.append(c); i += 1; continue
        if c == ";" and not in_dollar and not in_str:
            s = "".join(buf).strip()
            if s:
                stmts.append(s)
            buf = []; i += 1; continue
        buf.append(c); i += 1
    if "".join(buf).strip():
        stmts.append("".join(buf).strip())
    return stmts

with open("../advanced_module/continuity_assets.sql") as f:
    sql_text = f.read().replace("{{CATALOG}}", CATALOG).replace("{{SCHEMA}}", SCHEMA)

for stmt in split_sql(sql_text):
    label = " ".join(stmt.split())[:70]
    print(f"running: {label} ...")
    spark.sql(stmt)
print("\n✅ advanced module created")
display(spark.sql(f"SELECT ROUND(MEASURE(`PCP Continuity Ratio`)*100,1) AS pcp_continuity_pct, "
                  f"MEASURE(`Total Standard Visits`) AS standard_visits FROM {FQ('pcp_continuity_metrics')}"))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 3 · Import + publish the AI/BI dashboard
# MAGIC Reads `dashboard/workshop.lvdash.json`, fills tokens, and creates + publishes it via the SDK.
# MAGIC (Creates a new dashboard each run.)

# COMMAND ----------

import json

with open("../dashboard/workshop.lvdash.json") as f:
    dash = f.read()
for tok, val in {"{{CATALOG}}": CATALOG, "{{SCHEMA}}": SCHEMA, "{{CLIENT_NAME}}": CLIENT,
                 "{{PROCEDURE_EXAMPLE}}": PROC_EX, "{{PROCEDURE_CODE}}": PROC_CODE}.items():
    dash = dash.replace(tok, val)

created = w.api_client.do("POST", "/api/2.0/lakeview/dashboards", body={
    "display_name": f"Analyst 101 — Encounters & Outcomes ({CLIENT})",
    "warehouse_id": WAREHOUSE,
    "parent_path": PARENT,
    "serialized_dashboard": dash,
})
DASHBOARD_ID = created["dashboard_id"]
w.api_client.do("POST", f"/api/2.0/lakeview/dashboards/{DASHBOARD_ID}/published",
                body={"warehouse_id": WAREHOUSE})
host = w.config.host.rstrip("/")
print(f"✅ dashboard published: {host}/dashboardsv3/{DASHBOARD_ID}/published")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 4 · Create the Genie space
# MAGIC Builds the space on the 9 star-schema objects, registers the metric view + 3 functions as
# MAGIC trusted assets, sets the instructions + sample questions, and creates it via the SDK.
# MAGIC (Creates a new space each run.)

# COMMAND ----------

import uuid
_id = lambda: uuid.uuid4().hex

instructions = f"""This Genie space answers questions about synthetic hospital encounters. There is no PHI.

Data model:
- fact_encounters is the central fact table, one row per patient encounter.
- Join to dim_provider on provider_id, dim_facility on facility_id, dim_patient on patient_id,
  dim_visit_type on visit_type_id, dim_diagnosis on primary_icd10_code = icd10_code, and
  dim_procedure on primary_procedure_code = procedure_code. (These foreign keys are already defined.)

Metric definitions (express all rates as a percentage from 0 to 100):
- Readmission rate = AVG(readmitted_30d) * 100
- Mortality rate = AVG(mortality_flag) * 100
- Complication rate = AVG(complication_flag) * 100
- Average length of stay = AVG(length_of_stay_days), in days

PCP continuity of care:
- A "standard visit" is an encounter whose visit type has is_standard = true.
- PCP continuity = the share of a patient's standard visits handled by that patient's assigned PCP
  (dim_patient.assigned_pcp_id), expressed as a percentage.
- Prefer the pcp_continuity_metrics metric view for continuity rollups (use MEASURE() on its measures).
- The SQL functions pcp_continuity_ratio(), pcp_continuity_by_provider(), and standard_visit_count()
  are the trusted way to compute continuity; use them rather than hand-rolling the logic.

Conventions:
- When ranking providers or facilities by a rate, only include those with at least 200 encounters
  unless the user asks otherwise.
- Show plain-language names in results (provider_name, facility_name, region, clinical_category,
  procedure_description), not the id columns.
- "{PROC_EX}" means primary_procedure_code = '{PROC_CODE}'.
- Round rates to one decimal place and currency to whole dollars."""

tables = sorted([FQ(o) for o in ["fact_encounters", "dim_patient", "dim_provider", "dim_facility",
                                 "dim_visit_type", "dim_diagnosis", "dim_procedure",
                                 "encounters_enriched", "pcp_continuity_metrics"]])
functions = sorted(([{"id": _id(), "identifier": FQ(fn)}
                     for fn in ["pcp_continuity_ratio", "pcp_continuity_by_provider", "standard_visit_count"]]),
                   key=lambda x: (x["id"], x["identifier"]))
questions = [
    "How many encounters were there in 2024 by region?",
    "Which 10 providers have the highest 30-day readmission rate, with at least 200 encounters?",
    f"What is the average length of stay for a {PROC_EX}?",
    "Show the monthly encounter volume trend for the last 2 years.",
    "Which facilities have the highest complication rate?",
    "Compare mortality rate by clinical category.",
    "What is the average total paid per encounter by payer type?",
    "What is the overall PCP continuity rate across all standard visits?",
]

serialized_space = json.dumps({
    "version": 2,
    "config": {"sample_questions": [{"id": _id(), "question": [q]} for q in questions]},
    "data_sources": {"tables": [{"identifier": t} for t in tables]},
    "instructions": {
        "text_instructions": [{"id": _id(), "content": instructions.splitlines(keepends=True)}],
        "sql_functions": functions,
    },
})

space = w.api_client.do("POST", "/api/2.0/genie/spaces", body={
    "title": f"Analyst 101 & Databricks Day — Encounters & PCP Continuity ({CLIENT})",
    "description": "Synthetic hospital encounters (no PHI) for the Analyst 101 workshop and Databricks Day.",
    "warehouse_id": WAREHOUSE,
    "serialized_space": serialized_space,
})
SPACE_ID = space.get("space_id") or space.get("id")
print(f"✅ Genie space created: {host}/genie/rooms/{SPACE_ID}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 5 · Grant the attendee group (one-time)
# MAGIC Lets attendees create their own ETL schema and read the shared dataset. Edit the group widget
# MAGIC if your group has a different name. (Skips gracefully if the group doesn't exist yet.)

# COMMAND ----------

grants = [
    f"GRANT USE CATALOG ON CATALOG {CATALOG} TO `{GROUP}`",
    f"GRANT CREATE SCHEMA ON CATALOG {CATALOG} TO `{GROUP}`",
    f"GRANT USE SCHEMA, SELECT ON SCHEMA {CATALOG}.{SCHEMA} TO `{GROUP}`",
]
for g in grants:
    try:
        spark.sql(g); print("✅", g)
    except Exception as e:
        print("⚠️ skipped (create the group first, then re-run this cell):", g, "\n   ", str(e).splitlines()[0])

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 6 · Verify (smoke test)
# MAGIC If these match, the build is sound and the workshop is ready.

# COMMAND ----------

display(spark.sql(f"""
SELECT
  (SELECT COUNT(*) FROM {FQ('fact_encounters')})                                        AS encounters,
  (SELECT COUNT(*) FROM {FQ('dim_provider')})                                           AS providers,
  ROUND((SELECT MEASURE(`PCP Continuity Ratio`) FROM {FQ('pcp_continuity_metrics')})*100,1) AS pcp_continuity_pct,
  (SELECT ROUND(AVG(length_of_stay_days),2) FROM {FQ('fact_encounters')}
     WHERE primary_procedure_code = '{PROC_CODE}')                                       AS headline_surgery_los
"""))
print(f"Dashboard : {host}/dashboardsv3/{DASHBOARD_ID}/published")
print(f"Genie     : {host}/genie/rooms/{SPACE_ID}")
print(f"\nExpected: ~80000 encounters, PCP continuity ~76% (pediatric), and a non-null LOS for the headline surgery ({PROC_EX}).")
