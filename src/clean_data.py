
import os
import re
import pandas as pd

from dotenv import load_dotenv
from sqlalchemy import create_engine, URL


# =====================================
# 1. CONNECT TO POSTGRESQL
# =====================================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

load_dotenv(os.path.join(BASE_DIR, ".env"))

engine = create_engine(
    URL.create(
        "postgresql+psycopg2",
        username=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT")),
        database=os.getenv("DB_NAME")
    )
)


# =====================================
# 2. READ RAW DATA
# =====================================

print("Reading raw earthquake data...")

df = pd.read_sql_query(
    "SELECT * FROM raw_data.earthquake_raw",
    engine
)

original_rows = len(df)

print("Original rows:", original_rows)


# =====================================
# 3. CLEANING
# =====================================

print("\n--- DATA CLEANING ---")

# 3.1 ตรวจสอบ Duplicate
duplicate_count = df.duplicated().sum()

df = df.drop_duplicates()

print("Duplicates removed:", duplicate_count)


# 3.2 แปลงวันที่เป็น Datetime
date_columns = [
    "source_origin_time",
    "trace_start_time"
]

for col in date_columns:
    df[col] = pd.to_datetime(
        df[col],
        errors="coerce"
    )

    print(f"Converted datetime: {col}")


# 3.3 แปลงคอลัมน์ที่ควรเป็นตัวเลข
numeric_columns = [
    "p_weight",
    "p_travel_sec",
    "s_weight",
    "source_depth_km",
    "source_magnitude",
    "source_latitude",
    "source_longitude",
    "receiver_latitude",
    "receiver_longitude",
    "source_distance_km",
    "source_distance_deg",
    "back_azimuth_deg",
    "source_error_sec",
    "source_gap_deg",
    "source_horizontal_uncertainty_km",
    "source_depth_uncertainty_km",
    "source_origin_uncertainty_sec"
]

for col in numeric_columns:
    df[col] = pd.to_numeric(
        df[col],
        errors="coerce"
    )


# 3.4 จัดการ Missing Values
# ไม่เติมค่าปลอมลงในข้อมูลทางธรณีวิทยา
missing_before = df.isna().sum().sum()

print("Missing values preserved:", missing_before)


# 3.5 ตรวจสอบค่าพิกัดที่อยู่นอกช่วง
df["invalid_source_coordinates"] = (
    ~df["source_latitude"].between(-90, 90)
    | ~df["source_longitude"].between(-180, 180)
)

df["invalid_receiver_coordinates"] = (
    ~df["receiver_latitude"].between(-90, 90)
    | ~df["receiver_longitude"].between(-180, 180)
)


# 3.6 ทำเครื่องหมายค่าที่ต้องตรวจสอบ
df["review_negative_depth"] = df["source_depth_km"] < 0

df["review_negative_magnitude"] = (
    df["source_magnitude"] < 0
)

print(
    "Negative depth records:",
    df["review_negative_depth"].sum()
)

print(
    "Negative magnitude records:",
    df["review_negative_magnitude"].sum()
)


# =====================================
# 4. TRANSFORM STRING ARRAY COLUMNS
# =====================================

# แปลง snr_db ซึ่งเก็บค่าเป็นข้อความ Array
# เช่น [56.8 55.4 47.4]
def calculate_snr_mean(value):

    if pd.isna(value):
        return None

    numbers = re.findall(
        r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?",
        str(value)
    )

    if not numbers:
        return None

    values = pd.to_numeric(
        numbers,
        errors="coerce"
    )

    return values.mean()


df["snr_db_mean"] = df["snr_db"].apply(
    calculate_snr_mean
)


# แปลง coda_end_sample
# เช่น [[2896.]] -> 2896.0
def extract_coda_value(value):

    if pd.isna(value):
        return None

    numbers = re.findall(
        r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?",
        str(value)
    )

    if not numbers:
        return None

    return float(numbers[0])


df["coda_end_sample_value"] = (
    df["coda_end_sample"].apply(extract_coda_value)
)


# =====================================
# 5. SAVE CLEANED DATA
# =====================================

print("\nSaving cleaned data...")

df.to_sql(
    name="earthquake_clean",
    con=engine,
    schema="production",
    if_exists="replace",
    index=False,
    chunksize=5000
)


# =====================================
# 6. GENERATE CLEANING REPORT
# =====================================

print("\n--- CLEANING REPORT ---")

print("Original rows:", original_rows)
print("Cleaned rows:", len(df))
print("Columns:", len(df.columns))
print("Duplicate removed:", duplicate_count)

print(
    "Missing values:",
    df.isna().sum().sum()
)

print("\n--- NEW COLUMNS ---")

print(
    df[
        [
            "snr_db_mean",
            "coda_end_sample_value",
            "invalid_source_coordinates",
            "invalid_receiver_coordinates",
            "review_negative_depth",
            "review_negative_magnitude"
        ]
    ].head()
)

print("\nCLEANING COMPLETED")

engine.dispose()
