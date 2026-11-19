
import os
import pandas as pd

from dotenv import load_dotenv
from sqlalchemy import create_engine, URL

# 1. โหลดค่าจาก .env
load_dotenv()

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

# 2. อ่านข้อมูลจาก PostgreSQL ด้วย Pandas
print("Reading earthquake data...")

df = pd.read_sql_query(
    "SELECT * FROM raw_data.earthquake_raw",
    engine
)

# 3. ตรวจสอบขนาดข้อมูล
print("\n--- DATASET SIZE ---")
print("Rows:", df.shape[0])
print("Columns:", df.shape[1])

# 4. ตรวจสอบชื่อคอลัมน์และชนิดข้อมูล
print("\n--- COLUMN INFORMATION ---")
print(df.dtypes.to_string())

# 5. ตรวจสอบ Missing Values
print("\n--- MISSING VALUES ---")
missing = pd.DataFrame({
    "Missing_Count": df.isna().sum(),
    "Missing_Percent": (df.isna().mean() * 100).round(2)
})
print(missing.to_string())

# 6. ตรวจสอบข้อมูลซ้ำ
print("\n--- DUPLICATE DATA ---")
print("Duplicate rows:", df.duplicated().sum())

# 7. ตรวจสอบจำนวนเหตุการณ์และสถานี
print("\n--- UNIQUE VALUES ---")

for col in ["source_id", "receiver_code"]:
    if col in df.columns:
        print(col, ":", df[col].nunique())

# 8. แสดงข้อมูลตัวอย่าง
print("\n--- FIRST 5 ROWS ---")
print(df.head().to_string())

# 9. ตรวจสอบค่าทางสถิติ
print("\n--- DESCRIPTIVE STATISTICS ---")
print(df.describe(include="all").to_string())

engine.dispose()

print("\nDATA PROFILING COMPLETED")
