import os
import sqlite3
from typing import Dict, Any, List, Optional
try:
    from .data_loader import locate_dataset, load_data_as_dicts, get_project_root
except ImportError:
    from data_loader import locate_dataset, load_data_as_dicts, get_project_root

DB_NAME = "swishops.db"

def get_db_path() -> str:
    """Returns absolute path to the SQLite database file."""
    root = get_project_root()
    return os.path.join(root, DB_NAME)

def get_connection(db_path: Optional[str] = None) -> sqlite3.Connection:
    """Returns a SQLite connection with row factory configured to Row."""
    if db_path is None:
        db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def init_db(db_path: Optional[str] = None, force_reload: bool = False) -> int:
    """
    Initializes SQLite database and populates the deliveries table from the real CSV.
    Uses parameterized queries and transaction batches for performance.
    """
    if db_path is None:
        db_path = get_db_path()

    conn = get_connection(db_path)
    cur = conn.cursor()

    # Check if table already exists and has records
    cur.execute("SELECT count(name) FROM sqlite_master WHERE type='table' AND name='deliveries'")
    table_exists = cur.fetchone()[0] > 0

    if table_exists and not force_reload:
        cur.execute("SELECT count(*) FROM deliveries")
        count = cur.fetchone()[0]
        if count > 0:
            conn.close()
            return count

    # Drop existing table if force_reload
    cur.execute("DROP TABLE IF EXISTS deliveries")

    # Create schema matching zomato_cleaned.csv columns exactly
    cur.execute("""
    CREATE TABLE deliveries (
        id TEXT PRIMARY KEY,
        delivery_person_id TEXT,
        delivery_person_age REAL,
        delivery_person_ratings REAL,
        restaurant_latitude REAL,
        restaurant_longitude REAL,
        delivery_location_latitude REAL,
        delivery_location_longitude REAL,
        order_date TEXT,
        time_ordered TEXT,
        time_order_picked TEXT,
        weather_conditions TEXT,
        road_traffic_density TEXT,
        vehicle_condition INTEGER,
        type_of_order TEXT,
        type_of_vehicle TEXT,
        multiple_deliveries REAL,
        festival TEXT,
        city TEXT,
        time_taken_min REAL,
        distance_km REAL,
        delivery_speed TEXT
    )
    """)

    # Indices for high-speed analytical queries
    cur.execute("CREATE INDEX IF NOT EXISTS idx_city ON deliveries (city)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_weather ON deliveries (weather_conditions)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_traffic ON deliveries (road_traffic_density)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_speed ON deliveries (delivery_speed)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_festival ON deliveries (festival)")

    # Load rows from real dataset
    records = load_data_as_dicts()
    insert_sql = """
    INSERT INTO deliveries (
        id, delivery_person_id, delivery_person_age, delivery_person_ratings,
        restaurant_latitude, restaurant_longitude, delivery_location_latitude, delivery_location_longitude,
        order_date, time_ordered, time_order_picked, weather_conditions,
        road_traffic_density, vehicle_condition, type_of_order, type_of_vehicle,
        multiple_deliveries, festival, city, time_taken_min, distance_km, delivery_speed
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """

    batch = []
    for r in records:
        batch.append((
            r.get("ID"),
            r.get("Delivery_person_ID"),
            r.get("Delivery_person_Age"),
            r.get("Delivery_person_Ratings"),
            r.get("Restaurant_latitude"),
            r.get("Restaurant_longitude"),
            r.get("Delivery_location_latitude"),
            r.get("Delivery_location_longitude"),
            r.get("Order_Date"),
            r.get("Time_Orderd"),
            r.get("Time_Order_picked"),
            r.get("Weather_conditions"),
            r.get("Road_traffic_density"),
            r.get("Vehicle_condition"),
            r.get("Type_of_order"),
            r.get("Type_of_vehicle"),
            r.get("multiple_deliveries"),
            r.get("Festival"),
            r.get("City"),
            r.get("time_taken_min"),
            r.get("distance_km"),
            r.get("delivery_speed"),
        ))

    cur.executemany(insert_sql, batch)
    conn.commit()
    inserted_count = len(batch)
    conn.close()
    return inserted_count


def get_overall_kpis(filters: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    """
    Computes core delivery operational KPIs directly from SQL.
    Supports optional filters: city, weather, traffic, festival.
    """
    conn = get_connection()
    cur = conn.cursor()

    where_clauses = ["1=1"]
    params = []

    if filters:
        if filters.get("city"):
            where_clauses.append("city = ?")
            params.append(filters["city"])
        if filters.get("weather"):
            where_clauses.append("weather_conditions = ?")
            params.append(filters["weather"])
        if filters.get("traffic"):
            where_clauses.append("road_traffic_density = ?")
            params.append(filters["traffic"])
        if filters.get("festival"):
            where_clauses.append("festival = ?")
            params.append(filters["festival"])

    where_sql = " AND ".join(where_clauses)

    query = f"""
    SELECT
        COUNT(*) as total_deliveries,
        ROUND(AVG(time_taken_min), 2) as avg_time_taken,
        ROUND(AVG(distance_km), 2) as avg_distance_km,
        ROUND(AVG(delivery_person_ratings), 2) as avg_driver_rating,
        ROUND(AVG(delivery_person_age), 1) as avg_driver_age,
        ROUND(AVG(multiple_deliveries), 2) as avg_multi_deliveries,
        ROUND(100.0 * SUM(CASE WHEN delivery_speed = 'Slow' THEN 1 ELSE 0 END) / COUNT(*), 2) as pct_slow,
        ROUND(100.0 * SUM(CASE WHEN delivery_speed = 'Fast' THEN 1 ELSE 0 END) / COUNT(*), 2) as pct_fast,
        ROUND(100.0 * SUM(CASE WHEN delivery_speed = 'Average' THEN 1 ELSE 0 END) / COUNT(*), 2) as pct_average
    FROM deliveries
    WHERE {where_sql}
    """
    cur.execute(query, params)
    row = cur.fetchone()
    conn.close()

    return dict(row) if row else {}


def get_traffic_weather_matrix() -> List[Dict[str, Any]]:
    """Cross-tabulated average delivery time and count by traffic density and weather conditions."""
    conn = get_connection()
    cur = conn.cursor()
    query = """
    SELECT
        road_traffic_density,
        weather_conditions,
        COUNT(*) as order_count,
        ROUND(AVG(time_taken_min), 2) as avg_time_min,
        ROUND(AVG(distance_km), 2) as avg_distance_km,
        ROUND(100.0 * SUM(CASE WHEN delivery_speed = 'Slow' THEN 1 ELSE 0 END) / COUNT(*), 1) as slow_pct
    FROM deliveries
    WHERE road_traffic_density != '' AND weather_conditions != ''
    GROUP BY road_traffic_density, weather_conditions
    ORDER BY avg_time_min DESC
    """
    cur.execute(query)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def get_traffic_breakdown() -> List[Dict[str, Any]]:
    """Performance metrics grouped by road traffic density."""
    conn = get_connection()
    cur = conn.cursor()
    query = """
    SELECT
        road_traffic_density,
        COUNT(*) as order_count,
        ROUND(AVG(time_taken_min), 2) as avg_time_min,
        ROUND(AVG(distance_km), 2) as avg_distance_km,
        ROUND(AVG(delivery_person_ratings), 2) as avg_rating,
        ROUND(100.0 * SUM(CASE WHEN delivery_speed = 'Slow' THEN 1 ELSE 0 END) / COUNT(*), 1) as pct_slow
    FROM deliveries
    WHERE road_traffic_density != ''
    GROUP BY road_traffic_density
    ORDER BY avg_time_min DESC
    """
    cur.execute(query)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def get_weather_breakdown() -> List[Dict[str, Any]]:
    """Performance metrics grouped by weather condition."""
    conn = get_connection()
    cur = conn.cursor()
    query = """
    SELECT
        weather_conditions,
        COUNT(*) as order_count,
        ROUND(AVG(time_taken_min), 2) as avg_time_min,
        ROUND(AVG(distance_km), 2) as avg_distance_km,
        ROUND(AVG(delivery_person_ratings), 2) as avg_rating,
        ROUND(100.0 * SUM(CASE WHEN delivery_speed = 'Slow' THEN 1 ELSE 0 END) / COUNT(*), 1) as pct_slow
    FROM deliveries
    WHERE weather_conditions != ''
    GROUP BY weather_conditions
    ORDER BY avg_time_min DESC
    """
    cur.execute(query)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def get_distance_buckets() -> List[Dict[str, Any]]:
    """Performance segmented by delivery distance tiers."""
    conn = get_connection()
    cur = conn.cursor()
    query = """
    SELECT
        CASE
            WHEN distance_km < 3.0 THEN 'Short (< 3 km)'
            WHEN distance_km >= 3.0 AND distance_km < 8.0 THEN 'Medium (3 - 8 km)'
            WHEN distance_km >= 8.0 AND distance_km < 15.0 THEN 'Long (8 - 15 km)'
            ELSE 'Very Long (> 15 km)'
        END as distance_tier,
        COUNT(*) as order_count,
        ROUND(AVG(time_taken_min), 2) as avg_time_min,
        ROUND(AVG(distance_km), 2) as avg_distance_km,
        ROUND(100.0 * SUM(CASE WHEN delivery_speed = 'Slow' THEN 1 ELSE 0 END) / COUNT(*), 1) as pct_slow
    FROM deliveries
    GROUP BY distance_tier
    ORDER BY avg_distance_km ASC
    """
    cur.execute(query)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def get_vehicle_performance() -> List[Dict[str, Any]]:
    """Impact of vehicle type and vehicle condition."""
    conn = get_connection()
    cur = conn.cursor()
    query = """
    SELECT
        type_of_vehicle,
        vehicle_condition,
        COUNT(*) as order_count,
        ROUND(AVG(time_taken_min), 2) as avg_time_min,
        ROUND(AVG(distance_km), 2) as avg_distance_km,
        ROUND(100.0 * SUM(CASE WHEN delivery_speed = 'Slow' THEN 1 ELSE 0 END) / COUNT(*), 1) as pct_slow
    FROM deliveries
    WHERE type_of_vehicle != ''
    GROUP BY type_of_vehicle, vehicle_condition
    ORDER BY avg_time_min DESC
    """
    cur.execute(query)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def get_city_performance() -> List[Dict[str, Any]]:
    """Performance comparison across city types."""
    conn = get_connection()
    cur = conn.cursor()
    query = """
    SELECT
        city,
        COUNT(*) as order_count,
        ROUND(AVG(time_taken_min), 2) as avg_time_min,
        ROUND(AVG(distance_km), 2) as avg_distance_km,
        ROUND(AVG(delivery_person_ratings), 2) as avg_rating,
        ROUND(100.0 * SUM(CASE WHEN delivery_speed = 'Slow' THEN 1 ELSE 0 END) / COUNT(*), 1) as pct_slow
    FROM deliveries
    WHERE city != ''
    GROUP BY city
    ORDER BY avg_time_min DESC
    """
    cur.execute(query)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def get_festival_impact() -> List[Dict[str, Any]]:
    """Comparison of performance during festival vs non-festival days."""
    conn = get_connection()
    cur = conn.cursor()
    query = """
    SELECT
        festival,
        COUNT(*) as order_count,
        ROUND(AVG(time_taken_min), 2) as avg_time_min,
        ROUND(AVG(distance_km), 2) as avg_distance_km,
        ROUND(AVG(multiple_deliveries), 2) as avg_multi_deliveries,
        ROUND(100.0 * SUM(CASE WHEN delivery_speed = 'Slow' THEN 1 ELSE 0 END) / COUNT(*), 1) as pct_slow
    FROM deliveries
    WHERE festival != ''
    GROUP BY festival
    """
    cur.execute(query)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def get_bottleneck_segments() -> List[Dict[str, Any]]:
    """
    Identifies specific operational bottleneck combinations with highest delay rates.
    Filters for combinations with statistically significant sample sizes (> 50 orders).
    """
    conn = get_connection()
    cur = conn.cursor()
    query = """
    SELECT
        road_traffic_density,
        weather_conditions,
        city,
        vehicle_condition,
        COUNT(*) as order_count,
        ROUND(AVG(time_taken_min), 2) as avg_time_min,
        ROUND(100.0 * SUM(CASE WHEN delivery_speed = 'Slow' THEN 1 ELSE 0 END) / COUNT(*), 1) as pct_slow
    FROM deliveries
    WHERE road_traffic_density != '' AND weather_conditions != '' AND city != ''
    GROUP BY road_traffic_density, weather_conditions, city, vehicle_condition
    HAVING COUNT(*) >= 50
    ORDER BY avg_time_min DESC
    LIMIT 10
    """
    cur.execute(query)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def get_filter_options() -> Dict[str, List[str]]:
    """Returns available distinct filter values for the dashboard UI."""
    conn = get_connection()
    cur = conn.cursor()

    options = {}
    for col, key in [
        ("city", "cities"),
        ("weather_conditions", "weather_conditions"),
        ("road_traffic_density", "traffic_densities"),
        ("festival", "festivals"),
        ("type_of_vehicle", "vehicles")
    ]:
        cur.execute(f"SELECT DISTINCT {col} FROM deliveries WHERE {col} IS NOT NULL AND {col} != '' ORDER BY {col}")
        options[key] = [r[0] for r in cur.fetchall()]

    conn.close()
    return options
