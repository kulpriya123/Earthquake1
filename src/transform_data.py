
import os
import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv

# 1. Load database configuration
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, ".env"))

# ใช้ค่าการเชื่อมต่อชุดเดียวกับไฟล์ clean_data.py
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME")

DATABASE_URL = (
    f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}"
    f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

engine = create_engine(DATABASE_URL)

# 2. Read cleaned data
print("Reading cleaned earthquake data...")

df = pd.read_sql(
    "SELECT * FROM production.earthquake_clean",
    engine
)

print("Original rows:", len(df))

# 3. Convert origin time to datetime
df["source_origin_time"] = pd.to_datetime(
    df["source_origin_time"],
    errors="coerce"
)

# 4. Extract year and month
df["origin_year"] = df["source_origin_time"].dt.year
df["origin_month"] = df["source_origin_time"].dt.month

df["year_month"] = (
    df["source_origin_time"].dt.to_period("M").astype("string")
)

# 5. Classify earthquake magnitude
df["source_magnitude"] = pd.to_numeric(
    df["source_magnitude"],
    errors="coerce"
)

df["magnitude_level"] = pd.cut(
    df["source_magnitude"],
    bins=[float("-inf"), 2, 4, 5, 6, float("inf")],
    labels=["Micro", "Minor", "Light", "Moderate", "Strong"],
    right=False
).astype("string").fillna("Unknown")

# 6. Classify earthquake depth
df["source_depth_km"] = pd.to_numeric(
    df["source_depth_km"],
    errors="coerce"
)

df["depth_level"] = "Unknown"

df.loc[
    df["source_depth_km"].lt(0),
    "depth_level"
] = "Review"

df.loc[
    df["source_depth_km"].ge(0)
    & df["source_depth_km"].lt(70),
    "depth_level"
] = "Shallow"

df.loc[
    df["source_depth_km"].ge(70)
    & df["source_depth_km"].lt(300),
    "depth_level"
] = "Intermediate"

df.loc[
    df["source_depth_km"].ge(300),
    "depth_level"
] = "Deep"

# 7. Save transformed data to PostgreSQL
print("Saving transformed data...")

df.to_sql(
    name="earthquake_transformed",
    con=engine,
    schema="production",
    if_exists="replace",
    index=False,
    chunksize=5000
)

# 8. Display summary
print("\n--- TRANSFORMATION SUMMARY ---")
print("Rows:", len(df))

print("\nMagnitude levels:")
print(df["magnitude_level"].value_counts(dropna=False))

print("\nDepth levels:")
print(df["depth_level"].value_counts(dropna=False))

print("\nYear and month examples:")
print(
    df[
        [
            "source_origin_time",
            "origin_year",
            "origin_month",
            "year_month",
            "magnitude_level",
            "depth_level"
        ]
    ].head(10)
)

print("\nTransformation completed!")


# --------------------------------
# 7. Aggregation
# --------------------------------

print("\nPerforming Aggregation...")

# One source_id represents one earthquake event
event_df = df.drop_duplicates(
    subset=["source_id"]
).copy()

# Monthly earthquake summary
monthly_summary = (
    event_df.groupby("year_month", dropna=False)
    .agg(
        event_count=("source_id", "nunique"),
        avg_magnitude=("source_magnitude", "mean"),
        max_magnitude=("source_magnitude", "max"),
        avg_depth_km=("source_depth_km", "mean")
    )
    .reset_index()
)

monthly_summary["avg_magnitude"] = (
    monthly_summary["avg_magnitude"].round(2)
)

monthly_summary["avg_depth_km"] = (
    monthly_summary["avg_depth_km"].round(2)
)

# Magnitude level summary
magnitude_summary = (
    event_df.groupby("magnitude_level", dropna=False)
    .agg(
        event_count=("source_id", "nunique"),
        avg_magnitude=("source_magnitude", "mean"),
        max_magnitude=("source_magnitude", "max")
    )
    .reset_index()
)

total_events = magnitude_summary["event_count"].sum()

magnitude_summary["percentage"] = (
    magnitude_summary["event_count"] / total_events * 100
).round(2)

# Save aggregation results
monthly_summary.to_sql(
    name="earthquake_monthly_summary",
    con=engine,
    schema="production",
    if_exists="replace",
    index=False
)

magnitude_summary.to_sql(
    name="earthquake_magnitude_summary",
    con=engine,
    schema="production",
    if_exists="replace",
    index=False
)

print("Monthly summary:", len(monthly_summary))
print("Magnitude summary:")
print(magnitude_summary.to_string(index=False))


# --------------------------------
# 8. Joining
# --------------------------------

print("\nPerforming Joining...")

# Create station DataFrame
station_df = df[
    [
        "network_code",
        "receiver_code",
        "receiver_type",
        "receiver_latitude",
        "receiver_longitude",
        "receiver_elevation_m"
    ]
].drop_duplicates(
    subset=["network_code", "receiver_code"]
)

# Create earthquake event DataFrame
event_columns = [
    "source_id",
    "source_origin_time",
    "source_latitude",
    "source_longitude",
    "source_depth_km",
    "source_magnitude",
    "magnitude_level",
    "depth_level"
]

earthquake_df = df[event_columns].drop_duplicates(
    subset=["source_id"]
)

# Combine station and earthquake data
joined_df = df[
    [
        "network_code",
        "receiver_code",
        "source_id",
        "p_travel_sec",
        "s_weight"
    ]
].merge(
    station_df,
    on=["network_code", "receiver_code"],
    how="left",
    validate="many_to_one"
).merge(
    earthquake_df,
    on="source_id",
    how="left",
    validate="many_to_one"
)

# Save joined data
joined_df.to_sql(
    name="earthquake_joined",
    con=engine,
    schema="production",
    if_exists="replace",
    index=False,
    chunksize=5000
)

print("Joined rows:", len(joined_df))
print("Joining completed!")
