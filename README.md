# Properties Search - ระบบค้นหาอสังหาริมทรัพย์ด้วย AI

โปรเจคนี้เป็นระบบค้นหาอสังหาริมทรัพย์แบบครบวงจร ที่ผสานเทคโนโลยี AI, Vector Search และ Backend API เข้าด้วยกัน

## 🎯 ภาพรวมระบบ

ระบบประกอบด้วย 2 ส่วนหลักที่ทำงานร่วมกัน:

1. **Python AI Service** (`mercilnew/`) - ประมวลผลการค้นหาด้วย AI และ Vector Database
2. **Node.js Backend** (`Team4-YDP-Backend/`) - จัดการ User Authentication และ Search History

**จุดเด่นของระบบ:**
- 🧠 ค้นหาด้วยภาษาธรรมชาติ (Natural Language Search)
- 🎯 เข้าใจความหมายของคำค้นหา (Semantic Search)
- 📍 วิเคราะห์ POI (Point of Interest) มากกว่า 30 ประเภท
- 🤖 สร้างคำอธิบายผลลัพธ์ด้วย AI (RAG)
- 🔐 ระบบ Authentication ที่ปลอดภัย
- 📊 บันทึกประวัติการค้นหา

## 📁 โครงสร้างโปรเจค

### 🐍 `mercilnew/` - Python AI Search Service
บริการ AI หลักสำหรับค้นหาอสังหาริมทรัพย์อัจฉริยะ

**คุณสมบัติหลัก:**
- 🤖 **AI Intent Detection** - วิเคราะห์ความต้องการจากคำค้นหาด้วย LLM (GPT-4o-mini)
- 🔍 **Vector Search** - ค้นหาด้วย Semantic Embedding (ChromaDB + Sentence Transformers)
- 📊 **Smart Ranking** - จัดอันดับผลลัพธ์ตามความเกี่ยวข้อง POI และ Lifestyle Score
- 🔐 **API Security** - ป้องกันด้วย Bearer Token Authentication
- 📝 **RAG Explanation** - สร้างคำอธิบายผลลัพธ์ด้วย AI

**เทคโนโลยี:**
- FastAPI, Uvicorn
- ChromaDB (Vector Database)
- Sentence Transformers (thenlper/gte-large)
- OpenRouter API (LLM)

**ไฟล์สำคัญ:**
- `api_service.py` - FastAPI Service หลัก (Port 8000)
- `search_pipeline.py` - AI Search Logic และ Ranking Engine
- `build_vectorstore.py` - สร้าง Vector Database จาก CSV
- `poi_fetcher.py` - ดึงข้อมูล POI จาก Google Maps API
- `npa_vectorstore/` - ChromaDB Vector Database
- `assets_rows_merged_with_poi.csv` - ข้อมูลทรัพย์สิน + POI (ไฟล์หลัก)

---

### 🟢 `Team4-YDP-Backend/` - Node.js Backend API
Backend API สำหรับจัดการ User Authentication และ Search History

**คุณสมบัติหลัก:**
- 🔐 **User Authentication** - ลงทะเบียน, Login, JWT Token
- 📜 **Search History** - บันทึกและจัดการประวัติการค้นหา
- 🔗 **AI Integration** - เชื่อมต่อกับ Python AI Service
- 🗄️ **MongoDB** - จัดเก็บข้อมูล User และ History

**เทคโนโลยี:**
- Express.js 5.1.0
- MongoDB + Mongoose 8.20.1
- JWT (jsonwebtoken)
- bcrypt (Password Hashing)
- Axios (HTTP Client)

**โครงสร้างภายใน:**
- `controllers/` - Business Logic (authController, searchController)
- `models/` - Database Schema (User, SearchHistory)
- `routes/` - API Routes (authRoutes, searchRoutes)
- `middleware/` - JWT Verification
- `config/` - Database Configuration

---

## 🚀 วิธีการใช้งาน

### ข้อกำหนดเบื้องต้น (Prerequisites)
- Python 3.8+ 
- Node.js 16+
- MongoDB (Local หรือ Cloud)
- API Keys:
  - OpenRouter API Key (สำหรับ LLM)
  - Google Maps API Key (สำหรับ POI - ถ้าต้องการดึงข้อมูลใหม่)

### 1. เริ่มต้น Python AI Service

```bash
# เข้าไปในโฟลเดอร์
cd mercilnew

# สร้าง Virtual Environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Mac/Linux

# ติดตั้ง Dependencies
pip install -r requirements.txt

# ตั้งค่า Environment Variables
# สร้างไฟล์ .env และใส่:
# MERCIL_API_KEY=your_secret_key
# OPENROUTER_API_KEY=your_openrouter_key

# รัน Service
python api_service.py
```
✅ Service จะรันที่: `http://localhost:8000`

### 2. เริ่มต้น Node.js Backend

```bash
# เข้าไปในโฟลเดอร์
cd Team4-YDP-Backend

# ติดตั้ง Dependencies
npm install

# ตั้งค่า Environment Variables
# สร้างไฟล์ .env และใส่:
# PORT=3000
# MONGODB_URI=mongodb://localhost:27017/team4_db
# JWT_SECRET=your_secret_key
# PYTHON_SERVICE_URL=http://localhost:8000/api/v1/search
# MERCIL_API_KEY=your_secret_key (ต้องตรงกับ Python)

# รัน Service (Development Mode)
npm run dev
```
✅ Service จะรันที่: `http://localhost:3000`

### 3. ทดสอบระบบ

**วิธีที่ 1: ใช้ Postman Collection**
1. Import ไฟล์ `Properties-Search-API.postman_collection.json` เข้า Postman
2. ทดสอบ API ตาม Collection ที่กำหนดไว้
3. Collection รวม: Authentication, Search, History Management

**วิธีที่ 2: ใช้ Swagger UI**
- เปิดเบราว์เซอร์: `http://localhost:8000/docs`
- ทดสอบ Python AI Service โดยตรง

**วิธีที่ 3: ใช้ cURL**
```bash
# ทดสอบ Python Service โดยตรง
curl -X POST http://localhost:8000/api/v1/search ^
  -H "Authorization: Bearer your_secret_key" ^
  -H "Content-Type: application/json" ^
  -d "{\"query\":\"คอนโดใกล้ BTS\",\"filters\":{}}"

# ทดสอบผ่าน Node.js Backend
# 1. ลงทะเบียน
curl -X POST http://localhost:3000/api/auth/register ^
  -H "Content-Type: application/json" ^
  -d "{\"username\":\"test\",\"email\":\"test@test.com\",\"password\":\"pass123\"}"

# 2. Login (จะได้ Token)
curl -X POST http://localhost:3000/api/auth/login ^
  -H "Content-Type: application/json" ^
  -d "{\"email\":\"test@test.com\",\"password\":\"pass123\"}"

# 3. ค้นหา (ใส่ Token ที่ได้)
curl -X GET "http://localhost:3000/api/search?q=คอนโดใกล้ BTS" ^
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 🔗 สถาปัตยกรรมระบบ (Architecture)

```
┌─────────────────────────────────────────────────────────────────┐
│                         User / Frontend                          │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│              Node.js Backend (Port 3000)                         │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  • JWT Authentication                                     │  │
│  │  • User Management                                        │  │
│  │  • Search History Management                             │  │
│  │  • API Gateway                                           │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────┬────────────────────────────────┬───────────────────┘
             │                                │
             ▼                                ▼
┌────────────────────────────┐   ┌──────────────────────────────┐
│  MongoDB                   │   │  Python AI Service (8000)    │
│  • Users Collection        │   │  ┌──────────────────────────┐│
│  • SearchHistory Collection│   │  │ • Intent Detection (LLM) ││
└────────────────────────────┘   │  │ • Vector Search          ││
                                 │  │ • Smart Ranking          ││
                                 │  │ • RAG Explanation        ││
                                 │  └──────────────────────────┘│
                                 └──────────────┬───────────────┘
                                                │
                                                ▼
                                 ┌──────────────────────────────┐
                                 │  ChromaDB Vector Database    │
                                 │  • Embeddings (1024D)        │
                                 │  • Metadata (Properties+POI) │
                                 └──────────────────────────────┘
```

### การทำงานของระบบ (Flow)

1. **User ส่ง Request** → Node.js Backend
2. **JWT Authentication** → ตรวจสอบ Token
3. **Forward Request** → Python AI Service
4. **Intent Detection** → วิเคราะห์คำค้นหาด้วย LLM
5. **Vector Search** → ค้นหาใน ChromaDB
6. **Smart Ranking** → คำนวณคะแนนและจัดอันดับ
7. **RAG Explanation** → สร้างคำอธิบายด้วย AI
8. **Save History** → บันทึกลง MongoDB
9. **Return Response** → ส่งกลับไปยัง User

---

## 📝 ตัวอย่างการใช้งาน

### ตัวอย่างคำค้นหาที่รองรับ

```
✅ "คอนโดใกล้ BTS ราคาไม่เกิน 3 ล้าน"
✅ "บ้านเดี่ยวสำหรับครอบครัว มีสวน เลี้ยงสัตว์ได้"
✅ "ทาวน์โฮมใกล้โรงเรียน ไม่เกิน 5 ล้าน"
✅ "อาคารชุดใกล้ห้าง มียิม ราคา 2-4 ล้าน"
✅ "บ้านแฝดใกล้โรงพยาบาล ไม่อยากอยู่ใกล้ตลาด"
```

### ขั้นตอนการใช้งาน

1. **ลงทะเบียน/Login** ผ่าน Node.js Backend (`/api/auth/register`, `/api/auth/login`)
2. **ค้นหาอสังหาฯ** ด้วย Natural Language (`/api/search?q=...`)
3. **ดูผลลัพธ์** พร้อมคำอธิบายจาก AI
   - คะแนนความเหมาะสม (Final Score)
   - เหตุผลที่แนะนำ (Reasons)
   - ข้อควรระวัง (Penalties)
   - คำอธิบายจาก AI (Summary)
4. **ตรวจสอบประวัติ** การค้นหาที่ผ่านมา (`/api/search/history`)

### ตัวอย่าง Response

```json
{
  "query": "คอนโดใกล้ BTS ราคาไม่เกิน 3 ล้าน",
  "intent_detected": {
    "asset_types": ["คอนโด"],
    "must_have": ["bts_station"],
    "price_range": { "max": 3000000 }
  },
  "results": [
    {
      "id": "8",
      "final_score": 0.92,
      "intent_score": 1.5,
      "summary": "คอนโดนี้ตรงใจมาก ใกล้ BTS เพียง 500 เมตร ราคา 776,000 บาท",
      "reasons": [
        "ตรงประเภท (อาคารชุด)",
        "ใกล้ BTS อารีย์ (500 ม.)"
      ],
      "penalties": [],
      "asset_details": {
        "name": "โครงการห้าดาวคอนโดมิเนียม",
        "price": 776000,
        "location": "กรุงเทพมหานคร",
        "bedroom": 1,
        "bathroom": 1
      }
    }
  ]
}
```

---

## 🔧 Troubleshooting

### ปัญหาที่พบบ่อย

**1. Python Service ไม่สามารถเริ่มได้**
- ตรวจสอบว่าติดตั้ง Dependencies ครบ: `pip install -r requirements.txt`
- ตรวจสอบว่า Port 8000 ว่าง
- ตรวจสอบว่ามี `npa_vectorstore/` และข้อมูลภายใน

**2. Node.js Backend เชื่อมต่อ MongoDB ไม่ได้**
- ตรวจสอบว่า MongoDB รันอยู่: `mongod --version`
- ตรวจสอบ `MONGODB_URI` ใน `.env`

**3. การค้นหาไม่ได้ผลลัพธ์**
- ตรวจสอบว่า Python Service รันอยู่
- ตรวจสอบว่า `MERCIL_API_KEY` ตรงกันทั้ง 2 Service
- ตรวจสอบว่ามี `OPENROUTER_API_KEY` และมี Credit

**4. Vector Database ไม่มีข้อมูล**
- สร้าง Vector DB ใหม่: `cd mercilnew && python build_vectorstore.py --csv_path assets_rows_merged_with_poi.csv`

## 📊 ข้อมูลเทคนิค

**Python AI Service:**
- Framework: FastAPI 0.104.1
- Vector DB: ChromaDB 0.4.18
- Embedding Model: thenlper/gte-large (1024D)
- LLM: GPT-4o-mini (via OpenRouter)

**Node.js Backend:**
- Framework: Express 5.1.0
- Database: MongoDB + Mongoose 8.20.1
- Authentication: JWT + bcrypt

**Data:**
- จำนวนทรัพย์สิน: ตรวจสอบใน ChromaDB
- POI Types: 30+ ประเภท
- Embedding Dimensions: 1024

## 📚 เอกสารเพิ่มเติม

- [mercilnew/README.md](mercilnew/README.md) - คู่มือ Python AI Service (ละเอียด)
- [Team4-YDP-Backend/README.md](Team4-YDP-Backend/README.md) - คู่มือ Node.js Backend (ละเอียด)

## 🤝 การพัฒนาต่อ

**Feature ที่สามารถเพิ่มได้:**
- 🎨 Frontend UI (React/Vue)
- 📱 Mobile App
- 🗺️ แสดงผลบนแผนที่
- 📸 Image Search
- 💬 Chatbot Interface
- 📈 Analytics Dashboard

 
 