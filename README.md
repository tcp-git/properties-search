# Properties Search - ระบบค้นหาอสังหาริมทรัพย์ด้วย AI

โปรเจคนี้เป็นระบบค้นหาอสังหาริมทรัพย์แบบครบวงจร ที่ผสานเทคโนโลยี AI, Vector Search และ Backend API เข้าด้วยกัน

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
- `api_service.py` - FastAPI Service หลัก
- `search_pipeline.py` - Logic การค้นหาและ Ranking
- `build_vectorstore.py` - สร้าง Vector Database
- `npa_vectorstore/` - ข้อมูล ChromaDB
- `poi_fetcher.py` - ดึงข้อมูล POI จาก Google Places

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

### 1. เริ่มต้น Python AI Service
```bash
cd mercilnew
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python api_service.py
```
Service จะรันที่: `http://localhost:8000`

### 2. เริ่มต้น Node.js Backend
```bash
cd Team4-YDP-Backend
npm install
npm run dev
```
Service จะรันที่: `http://localhost:3000`

---

## 🔗 API Flow

```
User → Node.js Backend → Python AI Service → ChromaDB
         (JWT Auth)        (Vector Search)    (Embeddings)
              ↓
         MongoDB
      (Save History)
```

---

## 📝 ตัวอย่างการใช้งาน

1. **ลงทะเบียน/Login** ผ่าน Node.js Backend
2. **ค้นหาอสังหาฯ** ด้วย Natural Language (เช่น "หาคอนโดใกล้ BTS ราคาไม่เกิน 3 ล้าน")
3. **ดูผลลัพธ์** พร้อมคำอธิบายจาก AI
4. **ตรวจสอบประวัติ** การค้นหาที่ผ่านมา

---

## 📚 เอกสารเพิ่มเติม

- [mercilnew/README.md](mercilnew/README.md) - คู่มือ Python AI Service
- [Team4-YDP-Backend/README.md](Team4-YDP-Backend/README.md) - คู่มือ Node.js Backend

---

## 📄 License

MIT