# Mercil AI Search Service

Python AI Service สำหรับค้นหาอสังหาริมทรัพย์ด้วย AI

## ฟีเจอร์

- 🤖 **AI Intent Detection** - ตรวจจับความต้องการจากคำค้นหา
- 🔍 **Vector Search** - ค้นหาด้วย Embedding และ ChromaDB
- 📊 **Ranking** - จัดอันดับผลลัพธ์ตามความเกี่ยวข้อง

## 🔄 หลักการทำงาน: จาก CSV สู่ Vector Database

### ขั้นตอนการเตรียมข้อมูล (Data Pipeline)

```
1. ข้อมูลดิบ (Raw Data)
   ↓
   data/assets_rows.csv
   - ข้อมูลทรัพย์สิน: ชื่อ, ราคา, ที่อยู่, พิกัด (lat/lon)
   - รายละเอียด: ห้องนอน, ห้องน้ำ, พื้นที่
   - ประเภท: คอนโด, บ้านเดี่ยว, ทาวน์โฮม

2. ดึงข้อมูล POI (Point of Interest)
   ↓
   poi_fetcher.py → Google Maps API
   - ค้นหา POI ใกล้เคียงแต่ละทรัพย์สิน (30+ ประเภท)
   - คำนวณระยะทาง (เมตร) จากทรัพย์สินไปยัง POI
   - บันทึกเป็น poi_results_enhanced.csv
   
   POI ที่ดึง:
   • Transportation: BTS, MRT, รถไฟ, ป้ายรถเมล์
   • Shopping: ห้าง, ตลาด, 7-11, ซุปเปอร์มาร์เก็ต
   • Services: โรงพยาบาล, โรงเรียน, สัตวแพทย์
   • Lifestyle: ร้านอาหาร, คาเฟ่, ยิม, สปา
   • Tourism: ชายหาด, วัด, พิพิธภัณฑ์, สนามกอล์ฟ

3. รวมข้อมูล (Merge)
   ↓
   assets_rows.csv + poi_results_enhanced.csv
   = assets_rows_merged_with_poi.csv
   
   โครงสร้างข้อมูล:
   - ข้อมูลทรัพย์สิน (id, name, price, location, ...)
   - ระยะทาง POI (bts_station: 500, hospital: 1200, ...)
   - ชื่อ POI (bts_station_name: "BTS อารีย์", ...)

4. สร้าง Vector Database
   ↓
   build_vectorstore.py
   
   ขั้นตอน:
   a) อ่าน assets_rows_merged_with_poi.csv
   
   b) คำนวณ Lifestyle Score (0-10)
      - วิเคราะห์ระยะทาง POI แต่ละประเภท
      - ใช้ POI Config (radius, weight, curve)
      - ยิ่งใกล้ POI สำคัญ = คะแนนสูง
      
   c) สร้าง Text สำหรับ Embedding
      text = "ชื่อทรัพย์สิน | ประเภท | รายละเอียด"
      ตัวอย่าง: "คอนโด ดิ เอส สุขุมวิท | อาคารชุด | ใกล้ BTS..."
      
   d) แปลง Text → Vector (Embedding)
      - ใช้ Sentence Transformers (thenlper/gte-large)
      - แปลงข้อความเป็นตัวเลข 1024 มิติ
      - Vector นี้แทนความหมายของทรัพย์สิน
      
   e) บันทึกลง ChromaDB
      ↓
      npa_vectorstore/
      ├── chroma.sqlite3        # Database หลัก
      └── [collection folders]  # Embeddings + Metadata
      
      ข้อมูลที่เก็บ:
      • Embeddings (Vector 1024 มิติ)
      • Metadata (ข้อมูลทั้งหมดจาก CSV)
        - id, name, price, location
        - asset_type_id (สำคัญ! ใช้กรอง)
        - ระยะทาง POI ทั้งหมด
        - lifestyle_score
        - pet_friendly

5. ใช้งานจริง (Runtime)
   ↓
   api_service.py + search_pipeline.py
   
   เมื่อ User ค้นหา "คอนโดใกล้ BTS ราคาไม่เกิน 3 ล้าน":
   
   a) Intent Detection (LLM)
      → { asset_types: ["คอนโด"], 
          must_have: ["bts_station"],
          price_range: { max: 3000000 } }
   
   b) Vector Search (ChromaDB)
      - แปลง Query → Vector
      - ค้นหา Vector ที่ใกล้เคียงที่สุด (Semantic Search)
      - ได้ผลลัพธ์ 100 รายการ
   
   c) Filtering & Ranking
      - กรองตาม asset_type_id, price
      - คำนวณ Intent Score (ตรงความต้องการไหม?)
      - รวมคะแนน: Intent (70%) + Semantic (20%) + Lifestyle (10%)
      - เรียงลำดับและเลือก Top 5
   
   d) RAG Explanation (LLM)
      - สร้างคำอธิบายแต่ละรายการ
      - อธิบายว่าทำไมถึงแนะนำ
   
   e) ส่ง Response กลับ
```

### 💡 ทำไมต้องใช้ Vector Database?

**ปัญหาของการค้นหาแบบเดิม (SQL LIKE):**
- ค้นหาได้แค่คำที่ตรงทุกตัวอักษร
- "คอนโดใกล้ BTS" ≠ "อาคารชุดใกล้รถไฟฟ้า" (แม้ความหมายเหมือนกัน)

**ข้อดีของ Vector Search:**
- เข้าใจความหมาย (Semantic Understanding)
- "คอนโดใกล้ BTS" ≈ "อาคารชุดใกล้รถไฟฟ้า" ≈ "ห้องชุดติด BTS"
- ค้นหาได้แม้ไม่มีคำตรงกัน
- รองรับภาษาไทยได้ดี

**ตัวอย่างการทำงาน:**
```
Query: "บ้านหรูสำหรับครอบครัว"
→ Vector: [0.23, -0.45, 0.67, ...]

ค้นหาใน ChromaDB:
→ บ้านเดี่ยว 4 ห้องนอน (Vector ใกล้เคียง 0.89)
→ บ้านแฝดพื้นที่กว้าง (Vector ใกล้เคียง 0.85)
→ คอนโด 1 ห้องนอน (Vector ห่าง 0.32) ❌
```

## เริ่มต้นใช้งาน

### 1. สร้าง Virtual Environment
```bash
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Mac/Linux
```

### 2. ติดตั้ง Dependencies
```bash
pip install -r requirements.txt
```

### 3. ตั้งค่า Environment (.env)
สร้างไฟล์ `.env` และตั้งค่า API Keys:
```env
MERCIL_API_KEY=your_secret_key_here
OPENROUTER_API_KEY=your_openrouter_key
GOOGLE_MAPS_API_KEY=your_google_maps_key
```

**คำอธิบาย Environment Variables:**
- `MERCIL_API_KEY` - API Key สำหรับป้องกัน API (ใช้ร่วมกับ Node.js Backend)
- `OPENROUTER_API_KEY` - API Key สำหรับเรียกใช้ LLM (Intent Detection & RAG)
- `GOOGLE_MAPS_API_KEY` - API Key สำหรับดึงข้อมูล POI (ใช้กับ poi_fetcher.py)

### 4. รัน Service
```bash
python api_service.py
```

Service จะรันที่: `http://localhost:8000`

## API Endpoint

### Search
```
POST /api/v1/search
Authorization: Bearer YOUR_API_KEY
Content-Type: application/json

{
  "query": "หาคอนโดใกล้ BTS ราคาไม่เกิน 3 ล้าน",
  "filters": {}
}
```

### Response
```json
{
  "query": "หาคอนโดใกล้ BTS ราคาไม่เกิน 3 ล้าน",
  "intent_detected": {
    "property_type": "คอนโด",
    "near_bts": true,
    "price_max": 3000000
  },
  "results": [
    {
      "id": "prop_001",
      "name": "The Condo Sukhumvit",
      "price": 2800000,
      "score": 0.95
    }
  ]
}
```

## ทดสอบ API

### Swagger UI
เปิดเบราว์เซอร์: `http://localhost:8000/docs`

### cURL
```bash
curl -X POST http://localhost:8000/api/v1/search ^
  -H "Authorization: Bearer your_api_key" ^
  -H "Content-Type: application/json" ^
  -d "{\"query\":\"คอนโดใกล้ BTS\",\"filters\":{}}"
```

## โครงสร้างโปรเจค

```
mercilnew/
│
├── 🚀 Service Files (Production)
│   ├── api_service.py              # FastAPI Service หลัก
│   └── search_pipeline.py          # AI Search Logic & Ranking
│
├── 🔧 Data Preparation (Setup)
│   ├── poi_fetcher.py              # ดึงข้อมูล POI จาก Google Maps
│   └── build_vectorstore.py        # สร้าง Vector Database
│
├── 📊 Data Files
│   ├── assets_rows_merged_with_poi.csv          # ข้อมูลหลัก (Properties + POI)
│   ├── properties_with_scores_and_features.csv  # ข้อมูล + Lifestyle Score
│   ├── poi_results.csv                          # POI พื้นฐาน
│   ├── poi_results_enhanced.csv                 # POI เต็ม (30+ types)
│   ├── poi_cache.json                           # Cache POI พื้นฐาน
│   └── poi_cache_enhanced.json                  # Cache POI เต็ม
│
├── 🗄️ Folders
│   ├── npa_vectorstore/            # ChromaDB Vector Database
│   ├── data/                       # ข้อมูลดิบ (Raw CSV)
│   ├── cache/                      # Cache ชั่วคราว
│   ├── venv/                       # Python Virtual Environment
│   └── __pycache__/                # Python Bytecode Cache
│
├── ⚙️ Configuration
│   ├── requirements.txt            # Python Dependencies
│   ├── .env                        # Environment Variables (ไม่ commit)
│   └── .gitignore                  # Git Ignore Rules
│
└── 📖 Documentation
    └── README.md                   # คู่มือนี้
```

### 📂 ไฟล์หลัก (Core Files)

#### 🚀 Service Files
- **`api_service.py`** - FastAPI Service หลัก
  - รับ HTTP Request จาก Client
  - ตรวจสอบ Bearer Token Authentication
  - เรียกใช้ `search_pipeline.py` เพื่อประมวลผล
  - ส่ง Response กลับเป็น JSON

- **`search_pipeline.py`** - AI Search Logic และ Ranking Engine
  - **Intent Detection**: วิเคราะห์คำค้นหาด้วย LLM (GPT-4o-mini)
  - **Vector Search**: ค้นหาด้วย Semantic Embedding จาก ChromaDB
  - **Smart Ranking**: คำนวณคะแนนจาก Intent Score, Semantic Score, Lifestyle Score
  - **RAG Explanation**: สร้างคำอธิบายผลลัพธ์ด้วย AI
  - **POI Matching**: จับคู่ความต้องการกับ POI (BTS, ห้าง, โรงพยาบาล ฯลฯ)

#### 🔧 Data Preparation Files
- **`build_vectorstore.py`** - สร้าง Vector Database
  - อ่านข้อมูลจาก CSV (properties + POI)
  - คำนวณ Lifestyle Score จากระยะทาง POI
  - สร้าง Embeddings ด้วย Sentence Transformers
  - บันทึกลง ChromaDB พร้อม Metadata ครบถ้วน
  - รองรับ Asset Type Mapping และ Pet-Friendly Detection

- **`poi_fetcher.py`** - ดึงข้อมูล POI จาก Google Maps API
  - ค้นหา POI ใกล้เคียงแต่ละทรัพย์สิน (BTS, MRT, ห้าง, โรงพยาบาล ฯลฯ)
  - คำนวณระยะทางด้วย Distance Matrix API
  - รองรับ POI หลากหลายประเภท (30+ types)
  - มี Cache System เพื่อประหยัด API Quota
  - บันทึกผลลัพธ์เป็น CSV

### 📊 ไฟล์ข้อมูล (Data Files)

#### CSV Files
- **`assets_rows_merged_with_poi.csv`** - ข้อมูลทรัพย์สินรวม POI (ไฟล์หลักสำหรับสร้าง Vector DB)
- **`properties_with_scores_and_features.csv`** - ข้อมูลทรัพย์สินพร้อม Lifestyle Score
- **`poi_results.csv`** - ผลลัพธ์ POI จาก Google Maps (เวอร์ชันพื้นฐาน)
- **`poi_results_enhanced.csv`** - ผลลัพธ์ POI แบบเต็ม (รวม Tourism & Lifestyle POI)

#### JSON Files
- **`poi_cache.json`** - Cache ข้อมูล POI เพื่อประหยัด API calls
- **`poi_cache_enhanced.json`** - Cache ข้อมูล POI แบบเต็ม

### 🗄️ โฟลเดอร์

- **`npa_vectorstore/`** - ChromaDB Vector Database
  - เก็บ Embeddings และ Metadata ของทรัพย์สินทั้งหมด
  - ใช้สำหรับ Semantic Search

- **`data/`** - ข้อมูลดิบ (Raw Data)
  - ไฟล์ CSV ต้นฉบับก่อนประมวลผล

- **`cache/`** - ไฟล์ Cache ชั่วคราว

- **`venv/`** - Python Virtual Environment

- **`__pycache__/`** - Python Bytecode Cache

### ⚙️ ไฟล์ Configuration

- **`requirements.txt`** - Python Dependencies
  ```
  fastapi==0.104.1
  uvicorn==0.24.0
  chromadb==0.4.18
  sentence-transformers==2.2.2
  requests==2.31.0
  pandas==2.1.3
  python-dotenv==1.0.0
  googlemaps==4.10.0
  tqdm==4.66.1
  ```

- **`.env`** - Environment Variables (ไม่ commit ลง Git)
  ```env
  MERCIL_API_KEY=your_secret_key_here
  OPENROUTER_API_KEY=your_openrouter_key
  GOOGLE_MAPS_API_KEY=your_google_maps_key
  ```

- **`.gitignore`** - ไฟล์ที่ไม่ต้อง commit
  ```
  venv/
  __pycache__/
  .env
  *.pyc
  cache/
  *.log
  .DS_Store
  ```

### 📖 เอกสาร

- **`README.md`** - คู่มือการใช้งาน (ไฟล์นี้)

## 🔧 การสร้าง Vector Database (ครั้งแรก)

หากคุณต้องการสร้าง Vector Database ใหม่จากข้อมูล CSV:

### ขั้นตอนที่ 1: ดึงข้อมูล POI (ถ้ายังไม่มี)
```bash
python poi_fetcher.py
```
**หมายเหตุ:** ต้องมี `GOOGLE_MAPS_API_KEY` ใน `.env` และใช้เวลานาน (ขึ้นอยู่กับจำนวนทรัพย์สิน)

### ขั้นตอนที่ 2: สร้าง Vector Database
```bash
python build_vectorstore.py --csv_path assets_rows_merged_with_poi.csv
```

**Parameters:**
- `--csv_path` - ไฟล์ CSV ที่มีข้อมูลทรัพย์สิน + POI (required)
- `--db_path` - โฟลเดอร์สำหรับเก็บ Vector DB (default: npa_vectorstore)
- `--model` - Embedding model (default: thenlper/gte-large)
- `--collection` - ชื่อ Collection (default: npa_assets_v2)

**ตัวอย่าง:**
```bash
python build_vectorstore.py ^
  --csv_path assets_rows_merged_with_poi.csv ^
  --db_path npa_vectorstore ^
  --model thenlper/gte-large ^
  --collection npa_assets_v2
```

## 🔧 Troubleshooting

### ปัญหาที่พบบ่อย

**1. ChromaDB Collection Not Found**
```
Error: Collection 'npa_assets_v2' not found
```
**แก้ไข:**
- สร้าง Vector Database ใหม่: `python build_vectorstore.py --csv_path assets_rows_merged_with_poi.csv`
- ตรวจสอบว่าโฟลเดอร์ `npa_vectorstore/` มีอยู่

**2. OpenRouter API Error**
```
Error: OPENROUTER_API_KEY is not set
```
**แก้ไข:**
- ตั้งค่า `OPENROUTER_API_KEY` ใน `.env`
- ตรวจสอบว่า API Key ถูกต้องและมี Credit เหลืออยู่

**3. Embedding Model Download Failed**
```
Error: Failed to load embedding model
```
**แก้ไข:**
- ตรวจสอบการเชื่อมต่ออินเทอร์เน็ต
- Model จะถูกดาวน์โหลดอัตโนมัติครั้งแรก (~1.5 GB)
- ใช้เวลาประมาณ 5-10 นาที (ขึ้นอยู่กับความเร็วอินเทอร์เน็ต)

**4. Google Maps API Quota Exceeded**
```
Error: You have exceeded your daily request quota
```
**แก้ไข:**
- ตรวจสอบ Quota ที่ Google Cloud Console
- ใช้ Cache ที่มีอยู่แล้ว (poi_cache_enhanced.json)
- รอจนกว่า Quota จะ Reset (เที่ยงคืน Pacific Time)

**5. Port Already in Use**
```
Error: Address already in use
```
**แก้ไข:**
- ปิด Process ที่ใช้ Port 8000 อยู่
- Windows: `netstat -ano | findstr :8000` แล้ว `taskkill /PID <PID> /F`
- เปลี่ยน Port ใน `api_service.py` (บรรทัดสุดท้าย)

## 📊 ข้อมูลสถิติ

**Vector Database:**
- จำนวนทรัพย์สิน: ตรวจสอบด้วย `collection.count()`
- ขนาด Embedding: 1024 มิติ
- Model: thenlper/gte-large (Multilingual)

**POI Types (30+ ประเภท):**
- Transportation: 4 types (BTS, MRT, Train, Bus)
- Shopping: 4 types (Mall, Market, 7-11, Supermarket)
- Services: 4 types (Hospital, School, Veterinary, University)
- Lifestyle: 6 types (Restaurant, Cafe, Gym, Spa, Hotel, Community Mall)
- Tourism: 7 types (Beach, Temple, Museum, Tourist Attraction, Viewpoint, River, Golf)

## Technology Stack

- **FastAPI** 0.104.1 - Web framework
- **Uvicorn** 0.24.0 - ASGI server
- **ChromaDB** 0.4.18 - Vector database
- **Sentence Transformers** 2.2.2 - Embedding model (thenlper/gte-large)
- **Python-dotenv** 1.0.0 - Environment variables
- **Requests** 2.31.0 - HTTP client
- **Pandas** 2.1.3 - Data manipulation
- **Google Maps** 4.10.0 - POI fetching

## 📚 เอกสารเพิ่มเติม

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [ChromaDB Documentation](https://docs.trychroma.com/)
- [Sentence Transformers](https://www.sbert.net/)
- [OpenRouter API](https://openrouter.ai/docs)

## License

MIT
