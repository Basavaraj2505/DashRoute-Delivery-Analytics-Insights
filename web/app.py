import os
import sys
from flask import Flask, jsonify, request, render_template, send_from_directory

# Ensure project root is in sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.sqlite_layer import (
    init_db,
    get_overall_kpis,
    get_filter_options,
    get_bottleneck_segments,
    get_traffic_weather_matrix
)
from src.analysis import compute_comprehensive_summary
from src.visualization import get_all_dashboard_charts

app = Flask(__name__, template_folder=os.path.join(BASE_DIR, "templates"), static_folder=os.path.join(BASE_DIR, "static"))

@app.before_request
def setup_if_needed():
    # Guarantee DB is initialized on first request
    if not hasattr(app, "_db_initialized"):
        init_db()
        app._db_initialized = True

@app.route("/")
def index():
    """Serves the main DashRoute interactive dashboard."""
    return render_template("index.html")

@app.route("/api/health")
def health():
    """Service health and database status check."""
    return jsonify({
        "status": "healthy",
        "service": "DashRoute Analytics API",
        "version": "1.0.0"
    })

@app.route("/api/filters")
def api_filters():
    """Returns available distinct filter options."""
    try:
        options = get_filter_options()
        return jsonify(options)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/kpis")
def api_kpis():
    """
    Returns high-level KPIs with optional query parameters:
    - city
    - weather
    - traffic
    - festival
    """
    filters = {
        "city": request.args.get("city", "").strip(),
        "weather": request.args.get("weather", "").strip(),
        "traffic": request.args.get("traffic", "").strip(),
        "festival": request.args.get("festival", "").strip(),
    }
    # Remove empty filters
    active_filters = {k: v for k, v in filters.items() if v}
    try:
        kpis = get_overall_kpis(active_filters)
        return jsonify(kpis)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/charts")
def api_charts():
    """Returns Plotly-compatible JSON specifications for interactive charts."""
    try:
        charts = get_all_dashboard_charts()
        return jsonify(charts)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/summary")
def api_summary():
    """Returns the comprehensive analytical summary with root-cause insights and recommendations."""
    try:
        summary = compute_comprehensive_summary()
        return jsonify(summary)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/bottlenecks")
def api_bottlenecks():
    """Returns the top operational bottleneck segments."""
    try:
        bottlenecks = get_bottleneck_segments()
        return jsonify(bottlenecks)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    init_db()
    port = int(os.environ.get("PORT", 5000))
    print(f"\n==================================================")
    print(f">> DashRoute Dashboard starting on http://127.0.0.1:{port}")
    print(f"==================================================\n")
    app.run(host="127.0.0.1", port=port, debug=False)
