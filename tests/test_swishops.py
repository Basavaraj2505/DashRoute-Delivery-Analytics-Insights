import os
import sys
import pytest

# Add project root to sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.data_loader import locate_dataset, load_data_as_dicts, clean_row_data
from src.sqlite_layer import (
    init_db,
    get_db_path,
    get_connection,
    get_overall_kpis,
    get_traffic_breakdown,
    get_weather_breakdown,
    get_traffic_weather_matrix,
    get_bottleneck_segments,
    get_filter_options
)
from src.analysis import compute_comprehensive_summary
from src.visualization import get_all_dashboard_charts
from web.app import app

def test_dataset_location():
    """Verify that zomato_cleaned.csv is successfully located in project root."""
    csv_path = locate_dataset()
    assert os.path.exists(csv_path), "Dataset file does not exist"
    assert os.path.isfile(csv_path), "Dataset path is not a file"
    assert os.path.basename(csv_path) == "zomato_cleaned.csv"

def test_data_loader_parsing():
    """Verify data_loader parses rows accurately without modifying original CSV."""
    records = load_data_as_dicts()
    assert len(records) == 38964, f"Expected 38,964 rows, got {len(records)}"
    
    first = records[0]
    assert "ID" in first
    assert "time_taken_min" in first
    assert isinstance(first["time_taken_min"], (float, int))
    assert "distance_km" in first
    assert isinstance(first["distance_km"], (float, int))

def test_sqlite_db_initialization():
    """Verify SQLite database schema creation and row insertion."""
    count = init_db()
    assert count == 38964, f"Expected 38,964 rows in SQLite DB, got {count}"
    
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT count(*) FROM deliveries")
    db_count = cur.fetchone()[0]
    conn.close()
    assert db_count == 38964

def test_sql_kpi_queries():
    """Verify KPI queries with and without dynamic filters."""
    overall = get_overall_kpis()
    assert overall["total_deliveries"] == 38964
    assert overall["avg_time_taken"] > 20.0
    assert overall["avg_distance_km"] > 5.0
    assert 0.0 <= overall["pct_slow"] <= 100.0

    # Filtered test: Jam traffic
    jam_kpis = get_overall_kpis({"traffic": "Jam"})
    assert jam_kpis["total_deliveries"] > 0
    assert jam_kpis["avg_time_taken"] > overall["avg_time_taken"], "Jam traffic should be slower than average"

def test_traffic_weather_matrix():
    """Verify cross-tabulation matrix queries."""
    matrix = get_traffic_weather_matrix()
    assert len(matrix) > 0
    for row in matrix:
        assert "road_traffic_density" in row
        assert "weather_conditions" in row
        assert "avg_time_min" in row
        assert row["avg_time_min"] > 0

def test_bottleneck_segments():
    """Verify root-cause bottleneck query logic."""
    bottlenecks = get_bottleneck_segments()
    assert len(bottlenecks) > 0
    top = bottlenecks[0]
    assert "avg_time_min" in top
    assert "order_count" in top
    assert top["order_count"] >= 50

def test_analytical_summary_and_recommendations():
    """Verify high-level business intelligence generation."""
    summary = compute_comprehensive_summary()
    assert "kpis" in summary
    assert "insights" in summary
    assert len(summary["insights"]) >= 3
    assert "recommendations" in summary
    assert len(summary["recommendations"]) >= 4

    rec_ids = [r["id"] for r in summary["recommendations"]]
    assert "REC-01" in rec_ids

def test_visualization_charts():
    """Verify Plotly chart structures are valid JSON-serializable figures."""
    charts = get_all_dashboard_charts()
    assert "traffic_chart" in charts
    assert "weather_chart" in charts
    assert "traffic_weather_heatmap" in charts
    assert "distance_tiers_chart" in charts
    assert "vehicle_efficiency_chart" in charts

    for name, fig in charts.items():
        assert "data" in fig, f"{name} missing data property"
        assert "layout" in fig, f"{name} missing layout property"
        assert len(fig["data"]) > 0, f"{name} data array is empty"

def test_flask_api_endpoints():
    """Verify Flask HTTP API endpoints using Flask test client."""
    client = app.test_client()

    # GET /
    res_index = client.get("/")
    assert res_index.status_code == 200
    assert b"DashRoute" in res_index.data

    # GET /api/health
    res_health = client.get("/api/health")
    assert res_health.status_code == 200
    assert res_health.json["status"] == "healthy"
    assert res_health.json["service"] == "DashRoute Analytics API"

    # GET /api/filters
    res_filters = client.get("/api/filters")
    assert res_filters.status_code == 200
    assert "cities" in res_filters.json

    # GET /api/kpis
    res_kpis = client.get("/api/kpis?traffic=Jam")
    assert res_kpis.status_code == 200
    assert res_kpis.json["total_deliveries"] > 0

    # GET /api/charts
    res_charts = client.get("/api/charts")
    assert res_charts.status_code == 200
    assert "traffic_chart" in res_charts.json

    # GET /api/summary
    res_summary = client.get("/api/summary")
    assert res_summary.status_code == 200
    assert "recommendations" in res_summary.json

def test_powerbi_exports_and_consistency():
    """Verify Power BI export files, row counts, and numerical consistency with SQLite."""
    from powerbi.export_powerbi_data import export_all, EXPORT_DIR
    
    # Run export pipeline
    export_all()

    # Check files exist
    expected_files = [
        "fact_deliveries.csv",
        "dim_traffic.csv",
        "dim_weather.csv",
        "summary_traffic_weather.csv",
        "data_quality_report.csv",
        "export_metadata.json"
    ]
    for fn in expected_files:
        fp = os.path.join(EXPORT_DIR, fn)
        assert os.path.exists(fp), f"Expected Power BI export missing: {fp}"
        assert os.path.getsize(fp) > 0, f"Export file is empty: {fp}"

    # Verify fact_deliveries row count matches exactly
    import csv
    with open(os.path.join(EXPORT_DIR, "fact_deliveries.csv"), mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fact_rows = list(reader)
    assert len(fact_rows) == 38964, f"Expected 38,964 fact rows, got {len(fact_rows)}"

    # Verify numerical consistency with SQLite overall KPIs
    kpis = get_overall_kpis()
    fact_avg_time = sum(float(r["time_taken_min"]) for r in fact_rows if r.get("time_taken_min")) / len(fact_rows)
    assert abs(round(fact_avg_time, 2) - kpis["avg_time_taken"]) <= 0.05, "Power BI fact average duration does not match SQLite"

    # Verify DAX and Power Query M files exist and contain content
    pbi_dir = os.path.abspath(os.path.join(PROJECT_ROOT, "powerbi"))
    assert os.path.exists(os.path.join(pbi_dir, "measures.dax"))
    assert os.path.exists(os.path.join(pbi_dir, "power_query.m"))
    assert os.path.exists(os.path.join(pbi_dir, "data_dictionary.md"))
    assert os.path.exists(os.path.join(pbi_dir, "dashboard_design.md"))
