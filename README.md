# Earthquake Data Pipeline

โปรเจกต์ Data Pipeline สำหรับรวบรวม ทำความสะอาด แปลง และเผยแพร่ข้อมูลแผ่นดินไหว (Earthquake Data) โดยใช้ Python, Pandas, PostgreSQL, Docker และ Google Sheets พร้อมนำเสนอข้อมูลผ่าน Looker Studio

## 1. Technologies Used

- Python
- Pandas
- SQLAlchemy
- PostgreSQL
- Docker
- DBeaver
- Google Sheets API
- gspread
- Looker Studio

## 2. Project Structure

```text
321/
│
├── .venv/
├── data/
│   └── raw/
│       └── chunk2.csv
│
├── src/
│   ├── ingest.py
│   ├── clean_data.py
│   ├── transform_data.py
│   └── publish.py
│
├── .env
├── .gitignore
├── credentials.json
├── requirements.txt
├── README.md
└── run_pipeline.py
```

> หมายเหตุ: `.env` และ `credentials.json` เป็นไฟล์ตั้งค่าส่วนตัว ห้ามเผยแพร่ลง GitHub

## 3. Initial Setup (การติดตั้งครั้งแรก)

### 3.1 เปิดโฟลเดอร์โปรเจกต์

เปิด PowerShell แล้วใช้คำสั่ง:

```powershell
cd C:\Users\asus\Desktop\321
```

### 3.2 สร้าง Virtual Environment

หากยังไม่มี Virtual Environment ให้ใช้คำสั่ง:

```powershell
python -m venv .venv
```

### 3.3 เปิดใช้งาน Virtual Environment

```powershell
.\.venv\Scripts\Activate.ps1
```

เมื่อเปิดใช้งานสำเร็จ จะเห็น `(.venv)` หน้าบรรทัดคำสั่ง

### 3.4 ติดตั้ง Python Libraries

```powershell
python -m pip install -r requirements.txt
```

## 4. Configure Environment Variables

สร้างไฟล์ `.env` ที่โฟลเดอร์หลักของโปรเจกต์ และกำหนดค่าการเชื่อมต่อ PostgreSQL ดังนี้:

```env
DB_USER=your_database_user
DB_PASSWORD=your_database_password
DB_HOST=localhost
DB_PORT=5432
DB_NAME=your_database_name
```

แทนค่าตัวอย่างด้วยข้อมูลฐานข้อมูลที่ใช้งานจริง

## 5. Start PostgreSQL with Docker

เปิด Docker Desktop และรอให้ Docker ทำงานเรียบร้อย

จากนั้นเปิด PowerShell ในโฟลเดอร์โปรเจกต์

```powershell
docker compose up -d
```

ตรวจสอบสถานะ Container:

```powershell
docker compose ps
```

หากต้องการตรวจสอบ Log:

```powershell
docker compose logs
```

> คำสั่งนี้ใช้ได้เมื่อมีไฟล์ `docker-compose.yml` หรือ `compose.yaml` อยู่ในโฟลเดอร์ที่รันคำสั่ง

## 6. Run the Data Pipeline

เมื่อ PostgreSQL ทำงานแล้ว ให้เปิด Virtual Environment:

```powershell
.\.venv\Scripts\Activate.ps1
```

ตรวจสอบว่าเห็น `(.venv)` แล้วจึงรัน:

```powershell
python run_pipeline.py
```

ระบบจะเรียกใช้งานแต่ละขั้นตอนตามลำดับโดยอัตโนมัติ

### Pipeline Workflow

**Step 1: Data Ingestion**

ไฟล์ `src/ingest.py`

- อ่านข้อมูล CSV
- โหลดข้อมูลดิบเข้าสู่ PostgreSQL
- จัดเก็บใน Schema `raw_data`

**Step 2: Data Cleaning**

ไฟล์ `src/clean_data.py`

- ตรวจสอบและจัดการ Missing Values
- จัดการ Data Types
- ทำความสะอาดข้อมูล
- บันทึกข้อมูลใน Schema `production`

**Step 3: Transformation, Aggregation and Joining**

ไฟล์ `src/transform_data.py`

- สร้างคอลัมน์ใหม่
- จัดกลุ่มข้อมูล
- สรุปข้อมูลแผ่นดินไหว
- รวมข้อมูลจากตารางที่เกี่ยวข้อง
- บันทึกผลลัพธ์ใน Schema `production`

**Step 4: Publication**

ไฟล์ `src/publish.py`

- อ่านข้อมูลจาก PostgreSQL
- เชื่อมต่อ Google Sheets
- อัปโหลดข้อมูลไปยัง Worksheet `earthquake_joined`

### Expected Output

เมื่อทำงานสำเร็จ จะเห็นข้อความ:

```text
ALL PIPELINE STEPS COMPLETED SUCCESSFULLY!
```

## 7. View Data in PostgreSQL

สามารถเปิด DBeaver เพื่อเชื่อมต่อ PostgreSQL และตรวจสอบข้อมูลใน Schema ต่าง ๆ

ตารางหลักที่ใช้:

- `raw_data.earthquake_raw`
- `production.earthquake_clean`
- `production.earthquake_monthly_summary`
- `production.earthquake_magnitude_summary`
- `production.earthquake_joined`

## 8. View Data in Google Sheets

เปิด Google Sheets และเลือก Spreadsheet:

`Earthquake_Data`

เลือก Worksheet:

`earthquake_joined`

ข้อมูลที่เผยแพร่จะถูกนำไปใช้เป็นแหล่งข้อมูลสำหรับ Dashboard

## 9. View Dashboard in Looker Studio

เปิดเว็บไซต์:

https://lookerstudio.google.com/

เลือก Dashboard ของโปรเจกต์ Earthquake Data Pipeline

Dashboard ใช้ข้อมูลจาก Google Sheets เพื่อแสดงผลการวิเคราะห์ข้อมูลแผ่นดินไหวผ่าน Visualization

## 10. Stop PostgreSQL Docker Container

หากต้องการหยุด PostgreSQL ชั่วคราว:

```powershell
docker compose stop
```

หากต้องการเปิดใช้งานอีกครั้ง:

```powershell
docker compose start
```

หากต้องการหยุดและนำ Container รวมถึง Network ที่ Compose สร้างออก:

```powershell
docker compose down
```

> ไม่ควรใช้ `docker compose down -v` หากยังต้องการเก็บข้อมูล PostgreSQL ใน Volume ไว้

## 11. Daily Usage (คำสั่งสำหรับเปิดใช้งานประจำวัน)

เมื่อเคยติดตั้งทุกอย่างเรียบร้อยแล้ว สามารถเปิดใช้งานโปรเจกต์ด้วยขั้นตอนต่อไปนี้

**Step 1:** เปิด Docker Desktop

**Step 2:** เปิด PowerShell

**Step 3:** เข้าโฟลเดอร์โปรเจกต์

```powershell
cd C:\Users\asus\Desktop\321
```

**Step 4:** เปิด PostgreSQL

```powershell
docker compose up -d
```

**Step 5:** เปิด Virtual Environment

```powershell
.\.venv\Scripts\Activate.ps1
```

**Step 6:** รัน Pipeline

```powershell
python run_pipeline.py
```

**Step 7:** เปิด Google Sheets หรือ Looker Studio เพื่อดูข้อมูลและ Dashboard

---

## 12. Security Notes

- ไม่เผยแพร่ไฟล์ `.env`
- ไม่เผยแพร่ไฟล์ `credentials.json`
- ไม่เปิดเผย Database Password หรือ Google Service Account Private Key
- เพิ่มไฟล์ส่วนตัวลงใน `.gitignore`
- ควรเก็บข้อมูลสำรองของ PostgreSQL อย่างสม่ำเสมอ

## 13. Project Goal

สร้างระบบ Automated Data Pipeline ที่สามารถนำข้อมูลแผ่นดินไหวจาก CSV เข้าสู่ PostgreSQL ทำความสะอาดและแปลงข้อมูลด้วย Pandas เผยแพร่ผลลัพธ์ไปยัง Google Sheets และนำเสนอข้อมูลผ่าน Looker Studio Dashboard