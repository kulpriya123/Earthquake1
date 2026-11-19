
import os
import pandas as pd
import gspread

from sqlalchemy import create_engine, URL
from dotenv import load_dotenv
from gspread_dataframe import set_with_dataframe
import time

# --------------------------------
# 1. Load configuration
# --------------------------------

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

load_dotenv(os.path.join(BASE_DIR, ".env"))

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME")

# Google Sheets configuration
CREDENTIALS_FILE = os.path.join(
    BASE_DIR, "credentials.json"
)

SPREADSHEET_ID = "1QVzUpLb9GNdvrQVKwPncd6jwiswjtjhJ9ep0pGghALw"
WORKSHEET_NAME = "earthquake_joined"

# --------------------------------
# 2. Connect PostgreSQL
# --------------------------------

print("Connecting to PostgreSQL...")

if not all([DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME]):
    raise ValueError("Database configuration is incomplete. Check .env")

database_url = URL.create(
    drivername="postgresql+psycopg2",
    username=DB_USER,
    password=DB_PASSWORD,
    host=DB_HOST,
    port=int(DB_PORT),
    database=DB_NAME
)

engine = create_engine(database_url)

# --------------------------------
# 3. Read production data
# --------------------------------

print("Reading joined earthquake data...")

df = pd.read_sql(
    "SELECT * FROM production.earthquake_joined",
    engine
)

print("Total rows:", len(df))
print("Total columns:", len(df.columns))

# --------------------------------
# 4. Prepare data for Google Sheets
# --------------------------------

print("Preparing DataFrame...")

# Convert datetime columns to text
for col in df.select_dtypes(include=["datetime64[ns]", "datetimetz"]).columns:
    df[col] = df[col].astype("string").fillna("")

# Replace missing values with blank cells
df = df.astype(object).where(pd.notna(df), "")

# --------------------------------
# 5. Connect Google Sheets
# --------------------------------

print("Connecting to Google Sheets...")

if not os.path.exists(CREDENTIALS_FILE):
    raise FileNotFoundError(
        "credentials.json was not found in the project folder"
    )

gc = gspread.service_account(
    filename=CREDENTIALS_FILE
)

spreadsheet = gc.open_by_key(SPREADSHEET_ID)

worksheet = spreadsheet.worksheet(WORKSHEET_NAME)

# --------------------------------
# 6. Upload DataFrame
# --------------------------------

# 6. Upload data in chunks
print("Uploading data to Google Sheets...")

# Clear old data
worksheet.clear()

# Resize worksheet
worksheet.resize(
    rows=len(df) + 1,
    cols=len(df.columns)
)

# Upload in small batches
chunk_size = 1000

for start in range(0, len(df), chunk_size):
    end = min(start + chunk_size, len(df))

    chunk = df.iloc[start:end]

    # First batch includes column headers
    include_header = (start == 0)

    # Calculate starting row in Google Sheets
    start_row = start + 1

    set_with_dataframe(
        worksheet,
        chunk,
        row=start_row,
        col=1,
        include_index=False,
        include_column_header=include_header,
        resize=False
    )

    print(f"Uploaded rows: {end} / {len(df)}")

    # Avoid sending requests too quickly
    time.sleep(1.1)

print("Publication completed!")
print("Spreadsheet:", spreadsheet.url)
print("Uploaded rows:", len(df))
print("Uploaded columns:", len(df.columns))

engine.dispose()