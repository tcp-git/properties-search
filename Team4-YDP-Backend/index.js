// โหลด environment variables จากไฟล์ .env
import 'dotenv/config';
// โหลด Express framework
import express from 'express';
// โหลด routes สำหรับ authentication
import authRoutes from './routes/authRoutes.js';
// โหลด routes สำหรับ search
import searchRoutes from './routes/searchRoutes.js';
// โหลดฟังก์ชันเชื่อมต่อ MongoDB
import connectDB from './config/db.js';

// สร้าง Express application
const app = express();
// กำหนด port จาก environment variable หรือใช้ 3000 เป็นค่าเริ่มต้น
const port = process.env.PORT || 3000;

// เชื่อมต่อกับ MongoDB
connectDB();

// Middleware สำหรับแปลง JSON ใน request body
app.use(express.json());

// Route หลักสำหรับตรวจสอบว่า server ทำงาน
app.get('/', (req, res) => {
  res.send('Team 4 Backend API - AI Search Service');
});

// เชื่อมต่อ Authentication Routes (register, login, profile, logout)
app.use('/api/auth', authRoutes);

// เชื่อมต่อ Search Routes (search, history)
app.use('/api/search', searchRoutes);

// เริ่มต้น server
app.listen(port, () => {
  console.log(`🚀 Server กำลังทำงานที่ port ${port}`);
});