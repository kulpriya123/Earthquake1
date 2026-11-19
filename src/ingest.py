
import os
import pandas as pd

from dotenv import load_dotenv
from sqlalchemy import create_engine, URL, text


# 1. กำหนดตำแหน่งโฟลเดอร์โปรเจกต์
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# โหลด .env จากโฟลเดอร์หลักของโปรเจกต์โดยตรง
ENV_PATH = os.path.join(BASE_DIR, ".env")
load_dotenv(ENV_PATH)

DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")


# 2. กำหนดตำแหน่งไฟล์ CSV
CSV_PATH = os.path.join(
    BASE_DIR, "data", "raw", "chunk2.csv"
)


# 3. สร้างการเชื่อมต่อ PostgreSQL
connection_url = URL.create(
    drivername="postgresql+psycopg2",
    username=DB_USER,
    password=DB_PASSWORD,
    host=DB_HOST,
    port=int(DB_PORT),
    database=DB_NAME
)

engine = create_engine(connection_url)


# 4. ตรวจสอบ Database และสร้าง Schema
with engine.begin() as conn:

    print("\n--- DATABASE CONNECTION CHECK ---")

    result = conn.execute(text("""
        SELECT
            current_database(),
            current_user,
            current_schema()
    """))

    print("Database, User, Schema:", result.fetchone())

    # สร้าง Schema หากยังไม่มี
    conn.execute(text("""
        CREATE SCHEMA IF NOT EXISTS raw_data
    """))

    conn.execute(text("""
        CREATE SCHEMA IF NOT EXISTS production
    """))

    print("Schemas checked successfully!")

    # แสดง Schema ทั้งหมด
    schemas = conn.execute(text("""
        SELECT schema_name
        FROM information_schema.schemata
        ORDER BY schema_name
    """))

    print("Available schemas:")
    for schema in schemas:
        print(schema[0])


# ตรวจสอบไฟล์ CSV
if not os.path.exists(CSV_PATH):
    raise FileNotFoundError(f"CSV not found: {CSV_PATH}")

# นำข้อมูลเข้า PostgreSQL ทีละ 10,000 แถว
total_rows = 0
first_chunk = True

print("Starting Earthquake Data Ingestion...")

for chunk in pd.read_csv(CSV_PATH, chunksize=10000):

    chunk.to_sql(
        name="earthquake_raw",
        con=engine,
        schema="raw_data",
        if_exists="replace" if first_chunk else "append",
        index=False,
        method="multi",
        chunksize=1000
    )

    total_rows += len(chunk)
    first_chunk = False

    print(f"Imported {total_rows:,} rows")

# ตรวจสอบจำนวนข้อมูล
with engine.connect() as conn:
    result = conn.execute(text("""
        SELECT COUNT(*)
        FROM raw_data.earthquake_raw
    """))

    database_rows = result.scalar()

print("--------------------------------")
print("INGESTION COMPLETED")
print(f"Total imported rows: {total_rows:,}")
print(f"Database rows: {database_rows:,}")
print("--------------------------------")

engine.dispose()