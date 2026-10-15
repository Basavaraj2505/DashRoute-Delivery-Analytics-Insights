import os
import csv
import sys
from typing import Dict, Any, List, Optional, Tuple

def get_project_root() -> str:
    """Returns the absolute path to the project root directory."""
    # This file is in src/, so project root is one level up
    src_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.abspath(os.path.join(src_dir, ".."))

def locate_dataset(filename: str = "zomato_cleaned.csv") -> str:
    """
    Locates the dataset CSV file in expected candidate paths.
    Does not move or modify the original CSV.
    """
    root = get_project_root()
    candidates = [
        os.path.join(root, filename),
        os.path.join(root, "data", filename),
        os.path.join(os.getcwd(), filename),
        os.path.join(os.getcwd(), "data", filename),
        os.path.abspath(filename),
    ]
    for path in candidates:
        if os.path.exists(path) and os.path.isfile(path):
            return path
    raise FileNotFoundError(
        f"Could not locate '{filename}'. Searched candidate paths:\n" +
        "\n".join(f" - {p}" for p in candidates)
    )

def clean_row_data(row: Dict[str, Any]) -> Dict[str, Any]:
    """Cleans and casts individual fields in a row dictionary."""
    cleaned = dict(row)
    
    # Numeric float casts
    for float_col in [
        "Delivery_person_Age", "Delivery_person_Ratings",
        "Restaurant_latitude", "Restaurant_longitude",
        "Delivery_location_latitude", "Delivery_location_longitude",
        "multiple_deliveries", "distance_km"
    ]:
        val = cleaned.get(float_col)
        if val is None or str(val).strip() in ("", "nan", "NaN", "null", "None"):
            cleaned[float_col] = None
        else:
            try:
                cleaned[float_col] = float(str(val).strip())
            except (ValueError, TypeError):
                cleaned[float_col] = None

    # Time_taken (min)
    tt_val = cleaned.get("Time_taken (min)")
    if tt_val is not None:
        try:
            cleaned["time_taken_min"] = float(str(tt_val).strip())
        except (ValueError, TypeError):
            cleaned["time_taken_min"] = None
    else:
        cleaned["time_taken_min"] = None

    # Vehicle condition
    vc_val = cleaned.get("Vehicle_condition")
    if vc_val is not None:
        try:
            cleaned["Vehicle_condition"] = int(float(str(vc_val).strip()))
        except (ValueError, TypeError):
            cleaned["Vehicle_condition"] = 0
            
    # Strings stripped
    for str_col in [
        "ID", "Delivery_person_ID", "Order_Date", "Time_Orderd", "Time_Order_picked",
        "Weather_conditions", "Road_traffic_density", "Type_of_order",
        "Type_of_vehicle", "Festival", "City", "delivery_speed"
    ]:
        val = cleaned.get(str_col)
        if val is not None:
            cleaned[str_col] = str(val).strip()
        else:
            cleaned[str_col] = ""

    return cleaned

def load_data_as_dicts(csv_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """Loads CSV rows as a list of cleaned dictionaries using standard csv module."""
    if csv_path is None:
        csv_path = locate_dataset()
        
    records = []
    with open(csv_path, mode="r", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        for row in reader:
            records.append(clean_row_data(row))
    return records

def load_data_as_dataframe(csv_path: Optional[str] = None):
    """
    Loads dataset into a Pandas DataFrame if pandas is installed.
    Falls back to DataFrame constructed from dicts or raises ImportError if pandas is not installed.
    """
    if csv_path is None:
        csv_path = locate_dataset()

    try:
        import pandas as pd
    except ImportError:
        raise ImportError("Pandas is not installed. Use load_data_as_dicts() instead.")

    df = pd.read_csv(csv_path)
    
    # Standardize column naming if needed
    if "Time_taken (min)" in df.columns:
        df["time_taken_min"] = pd.to_numeric(df["Time_taken (min)"], errors="coerce")
    
    # Numeric conversions
    numeric_cols = [
        "Delivery_person_Age", "Delivery_person_Ratings",
        "Restaurant_latitude", "Restaurant_longitude",
        "Delivery_location_latitude", "Delivery_location_longitude",
        "multiple_deliveries", "distance_km", "Vehicle_condition"
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Clean text columns
    text_cols = [
        "Weather_conditions", "Road_traffic_density", "Type_of_order",
        "Type_of_vehicle", "Festival", "City", "delivery_speed"
    ]
    for col in text_cols:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()

    return df

if __name__ == "__main__":
    path = locate_dataset()
    print(f"Dataset located at: {path}")
    data = load_data_as_dicts(path)
    print(f"Loaded {len(data)} rows successfully via standard library.")
    try:
        df = load_data_as_dataframe(path)
        print(f"Loaded {len(df)} rows successfully via Pandas DataFrame.")
    except ImportError as e:
        print(f"Pandas notice: {e}")
