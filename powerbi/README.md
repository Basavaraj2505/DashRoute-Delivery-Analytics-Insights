# DashRoute — Microsoft Power BI Reporting Layer

This directory contains the complete Power BI enterprise analytics pipeline, star-schema data models, DAX measure definitions, Power Query scripts, and 4-page dashboard specification for **DashRoute**.

---

## 📁 Directory Structure

```
powerbi/
├── README.md                   # Complete developer setup and execution guide
├── export_powerbi_data.py       # Python pipeline exporting clean analytical datasets
├── data_dictionary.md          # Comprehensive metadata, schema, and column definitions
├── dashboard_design.md         # 4-page report design, visual layout, and theme specs
├── measures.dax                # Production-ready DAX measure library
├── power_query.m               # Copy-pasteable Power Query M ETL scripts
└── data/                       # Generated analysis-ready tables
    ├── fact_deliveries.csv     # 38,964 clean delivery transactions
    ├── dim_traffic.csv         # Traffic density ordinal dimension table
    ├── dim_weather.csv         # Weather severity dimension table
    ├── summary_traffic_weather.csv # Pre-aggregated cross-impact matrix
    ├── data_quality_report.csv # Data completeness and validation audit
    └── export_metadata.json    # Lineage, hash checksums, and export timestamps
```

---

## 🚀 End-to-End Workflow in Microsoft Power BI Desktop

Follow these steps to assemble the `DashRoute.pbix` report:

### Step 1: Generate or Refresh the Data Exports
Run the automated export script from PowerShell or Command Prompt:
```powershell
.\venv\Scripts\python.exe powerbi/export_powerbi_data.py
```
*This reads `zomato_cleaned.csv` in the project root, cleans missing and numeric formats, adds calculated attributes (`distance_tier`, `is_above_30min`, `vehicle_condition_label`), and writes verified CSVs into `powerbi/data/`.*

### Step 2: Open Power BI Desktop & Ingest Data
1. Launch **Microsoft Power BI Desktop**.
2. Click **Get Data &rarr; Text/CSV**.
3. Select `powerbi/data/fact_deliveries.csv` &rarr; click **Transform Data**.
4. In the Power Query Editor, click **New Source &rarr; Text/CSV** and import:
   - `powerbi/data/dim_traffic.csv`
   - `powerbi/data/dim_weather.csv`
   - `powerbi/data/summary_traffic_weather.csv`
   - `powerbi/data/data_quality_report.csv`
5. *(Optional but Recommended)*: Copy the optimized scripts from [power_query.m](file:///E:/food_distr_analysis/powerbi/power_query.m) into the **Advanced Editor** for each table to guarantee verified column data types.
6. Click **Close & Apply**.

### Step 3: Configure Star Schema Relationships
Navigate to the **Model View** tab in Power BI:
1. Connect `dim_traffic[road_traffic_density]` (1) &rarr; `fact_deliveries[Road_traffic_density]` (*)
   - Cardinality: **One to Many (1:*)**
   - Cross filter direction: **Single**
2. Connect `dim_weather[weather_conditions]` (1) &rarr; `fact_deliveries[Weather_conditions]` (*)
   - Cardinality: **One to Many (1:*)**
   - Cross filter direction: **Single**
3. Configure column sorting:
   - Select `dim_traffic[road_traffic_density]` &rarr; click **Sort by column** &rarr; select `traffic_sort_order`.
   - Select `dim_weather[weather_conditions]` &rarr; click **Sort by column** &rarr; select `weather_sort_order`.
   - Select `fact_deliveries[distance_tier]` &rarr; click **Sort by column** &rarr; select `distance_tier_order`.

### Step 4: Add the DAX Measures
1. Create a dedicated measures table or add measures to `fact_deliveries`.
2. Open [measures.dax](file:///E:/food_distr_analysis/powerbi/measures.dax) and copy the DAX measures:
   - `[Total Deliveries]`
   - `[Average Delivery Duration]`
   - `[Median Delivery Duration]`
   - `[P90 Delivery Duration]`
   - `[Deliveries Above 30 Min]`
   - `[% Above 30 Min]`
   - `[% Slow Delivery Rate]`
   - `[Average Courier Rating]`
   - `[Congestion Latency Penalty]`
   - `[Festival Impact Penalty]`

### Step 5: Build the 4 Report Pages
Follow the detailed visual positioning in [dashboard_design.md](file:///E:/food_distr_analysis/powerbi/dashboard_design.md):
- **Page 1 — Executive Overview:** High-level KPIs, 30-minute threshold violation rate, delivery duration histogram, and velocity donut chart.
- **Page 2 — Delivery Performance:** Traffic congestion bar + line chart, weather condition bar chart, distance bracket breakdown, and vehicle maintenance velocity.
- **Page 3 — Root Cause Analysis:** Cross-impact heatmap matrix (Traffic vs Weather), high-risk bottleneck table (sample size &ge; 50), and operational recommendations.
- **Page 4 — Data Quality:** Data completeness scorecard, missing-value audit, and operational scope boundaries.

### Step 6: Save and Maintain
1. Save your report as `DashRoute.pbix` in the project root or `powerbi/` folder.
2. Whenever the underlying dataset is updated, simply rerun `python powerbi/export_powerbi_data.py` and click **Refresh** on the Power BI Desktop Home ribbon.
