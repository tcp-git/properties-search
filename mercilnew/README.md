# Mercil AI Search Service

Python AI Service สำหรับค้นหาอสังหาริมทรัพย์ด้วย AI

## ฟีเจอร์

- 🤖 **AI Intent Detection** - ตรวจจับความต้องการจากคำค้นหา
- 🔍 **Vector Search** - ค้นหาด้วย Embedding และ ChromaDB
- 📊 **Ranking** - จัดอันดับผลลัพธ์ตามความเกี่ยวข้อง

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
```env
MERCIL_API_KEY=your_secret_key_here
```

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
├── api_service.py           # FastAPI Service
├── search_pipeline.py       # AI Search Logic
├── build_vectorstore.py     # สร้าง Vector Database
├── npa_vectorstore/         # ChromaDB Data
├── requirements.txt         # Dependencies
└── .env                     # Environment Variables
```

## Technology Stack

- **FastAPI** - Web framework
- **Uvicorn** - ASGI server
- **ChromaDB** - Vector database
- **Sentence Transformers** - Embedding model
- **Python-dotenv** - Environment variables

## License

MIT
