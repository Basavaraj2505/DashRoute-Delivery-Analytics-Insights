import sys
import os
import importlib.util
import traceback
import csv
import json

def main():
    output_lines = []
    
    def log(msg):
        print(msg)
        output_lines.append(str(msg))

    log(f"Python Executable: {sys.executable}")
    log(f"Python Version: {sys.version}")

    # 1. Check packages
    packages = ["pandas", "plotly", "flask", "pytest"]
    package_status = {}
    for pkg in packages:
        spec = importlib.util.find_spec(pkg)
        package_status[pkg] = "Available" if spec is not None else "Missing"
        log(f"Package '{pkg}': {package_status[pkg]}")

    # 2. Check disk space
    try:
        import shutil
        total, used, free = shutil.disk_usage("E:\\")
        log(f"Disk E: Free: {free / (1024**3):.2f} GB / Total: {total / (1024**3):.2f} GB")
    except Exception as e:
        log(f"Could not determine disk usage: {e}")

    # 3. Locate CSV
    csv_path = os.path.join(os.path.dirname(__file__), "zomato_cleaned.csv")
    if not os.path.exists(csv_path):
        csv_path = "E:\\food_distr_analysis\\zomato_cleaned.csv"
    
    log(f"CSV Path: {csv_path} (exists: {os.path.exists(csv_path)})")
    
    if os.path.exists(csv_path):
        log(f"CSV Size: {os.path.getsize(csv_path):,} bytes")
        
        has_pandas = package_status.get("pandas") == "Available"
        if has_pandas:
            try:
                import pandas as pd
                log("\n--- Profiling via Pandas ---")
                df = pd.read_csv(csv_path)
                log(f"Row count: {len(df)}")
                log(f"Column count: {len(df.columns)}")
                log(f"Columns: {list(df.columns)}")
                log("\nData Types:")
                for col, dt in df.dtypes.items():
                    log(f"  {col}: {dt}")
                log("\nMissing Values:")
                for col, mv in df.isnull().sum().items():
                    log(f"  {col}: {mv}")
                log(f"\nDuplicate rows count: {df.duplicated().sum()}")
                log("\nFirst 5 rows:")
                log(df.head(5).to_string())
            except Exception as e:
                log(f"Error loading via pandas: {e}")
                log(traceback.format_exc())
                has_pandas = False
        
        if not has_pandas:
            try:
                log("\n--- Profiling via standard csv module ---")
                with open(csv_path, mode="r", encoding="utf-8", errors="replace") as f:
                    reader = csv.reader(f)
                    header = next(reader)
                    rows = []
                    col_count = len(header)
                    row_count = 0
                    missing_counts = {col: 0 for col in header}
                    seen = set()
                    dups = 0
                    
                    for r in reader:
                        row_count += 1
                        if len(rows) < 5:
                            rows.append(r)
                        t = tuple(r)
                        if t in seen:
                            dups += 1
                        else:
                            seen.add(t)
                        for idx, val in enumerate(r):
                            if idx < col_count:
                                if val is None or val.strip() == "" or val.strip().lower() in ["nan", "null", "none"]:
                                    missing_counts[header[idx]] += 1

                log(f"Row count: {row_count}")
                log(f"Column count: {col_count}")
                log(f"Columns: {header}")
                log("\nMissing Values per column:")
                for col, cnt in missing_counts.items():
                    log(f"  {col}: {cnt}")
                log(f"\nDuplicate rows count (exact matches): {dups}")
                log("\nFirst 5 rows:")
                log("Header: " + " | ".join(header))
                for i, r in enumerate(rows):
                    log(f"Row {i+1}: " + " | ".join(r))
            except Exception as e:
                log(f"Error loading via csv module: {e}")
                log(traceback.format_exc())

    # Write full output to dataset_profile.txt
    profile_path = os.path.join(os.path.dirname(__file__), "dataset_profile.txt")
    with open(profile_path, "w", encoding="utf-8") as f:
        f.write("\n".join(output_lines))
    print(f"\nProfile successfully written to {profile_path}")

if __name__ == "__main__":
    main()
