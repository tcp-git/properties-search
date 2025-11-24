// นำเข้า SearchHistory model สำหรับจัดการประวัติการค้นหา
import SearchHistory from '../models/SearchHistory.js';
// นำเข้า axios สำหรับเรียก API ของ Python Service
import axios from 'axios';

// ฟังก์ชันสำหรับค้นหาข้อมูลด้วย AI
export const search = async (req, res) => {
  try {
    // รับคำค้นหา (q) และ filters จาก query parameters
    const { q, filters } = req.query;

    // ตรวจสอบว่ามีคำค้นหาหรือไม่
    if (!q) {
      return res.status(400).json({ message: 'กรุณาระบุคำค้นหา' });
    }

    // ดึง userId จาก JWT token ที่ถูก decode โดย middleware
    const userId = req.user.userId;
    // แปลง filters จาก JSON string เป็น object (ถ้ามี)
    const parsedFilters = filters ? JSON.parse(filters) : {};

    // ดึง URL ของ Python Service จาก environment variable
    const pythonServiceUrl = process.env.PYTHON_SERVICE_URL || 'http://localhost:8000/api/v1/search';
    // ดึง API Key สำหรับเชื่อมต่อกับ Python Service
    const apiKey = process.env.MERCIL_API_KEY;

    // เรียก Python Service เพื่อประมวลผลคำค้นหาด้วย AI
    const response = await axios.post(
      pythonServiceUrl,
      {
        query: q, // ส่งคำค้นหา
        filters: parsedFilters // ส่ง filters เพิ่มเติม
      },
      {
        headers: {
          'Authorization': `Bearer ${apiKey}`, // ใส่ API Key ใน header
          'Content-Type': 'application/json'
        }
      }
    );

    // บันทึกประวัติการค้นหาพร้อมผลลัพธ์ลงฐานข้อมูล
    try {
      await SearchHistory.create({
        userId, // ID ของผู้ใช้
        query: q, // คำค้นหา
        filters: parsedFilters, // filters ที่ใช้
        intentDetected: response.data.intent_detected || {}, // intent ที่ AI ตรวจจับได้
        resultsCount: response.data.results?.length || 0, // จำนวนผลลัพธ์
        results: response.data.results || [] // ผลลัพธ์ทั้งหมด
      });
    } catch (historyError) {
      // ถ้าบันทึกประวัติไม่สำเร็จ แสดง error แต่ไม่หยุดการทำงาน
      console.error('Error saving search history:', historyError);
    }

    // ส่งผลลัพธ์จาก AI กลับไปให้ client
    res.status(200).json(response.data);

  } catch (error) {
    // แสดง error ใน console
    console.error('Search Error:', error.message);
    // ถ้า error มาจาก Python Service ให้ส่ง error นั้นกลับไป
    if (error.response) {
      return res.status(error.response.status).json(error.response.data);
    }
    // ส่ง error response กลับไป
    res.status(500).json({ message: 'เกิดข้อผิดพลาดในการเชื่อมต่อกับบริการค้นหา', error: error.message });
  }
};

// ฟังก์ชันดูประวัติการค้นหาของผู้ใช้
export const getSearchHistory = async (req, res) => {
  try {
    // ดึง userId จาก JWT token
    const userId = req.user.userId;
    // รับค่า limit และ page จาก query parameters (ค่าเริ่มต้น: limit=20, page=1)
    const { limit = 20, page = 1 } = req.query;

    // คำนวณจำนวนรายการที่ต้อง skip สำหรับ pagination
    const skip = (parseInt(page) - 1) * parseInt(limit);

    // ค้นหาประวัติการค้นหาของผู้ใช้
    const history = await SearchHistory.find({ userId })
      .sort({ timestamp: -1 }) // เรียงจากใหม่ไปเก่า
      .limit(parseInt(limit)) // จำกัดจำนวนรายการ
      .skip(skip) // ข้ามรายการตาม pagination
      .select('-results'); // ไม่เอา results มาเพื่อลดขนาดข้อมูล

    // นับจำนวนประวัติทั้งหมดของผู้ใช้
    const total = await SearchHistory.countDocuments({ userId });

    // ส่งประวัติและข้อมูล pagination กลับไป
    res.status(200).json({
      history,
      pagination: {
        total, // จำนวนทั้งหมด
        page: parseInt(page), // หน้าปัจจุบัน
        limit: parseInt(limit), // จำนวนต่อหน้า
        totalPages: Math.ceil(total / parseInt(limit)) // จำนวนหน้าทั้งหมด
      }
    });

  } catch (error) {
    // แสดง error ใน console
    console.error('Get History Error:', error);
    // ส่ง error response กลับไป
    res.status(500).json({ message: 'เกิดข้อผิดพลาดในการดึงประวัติ', error: error.message });
  }
};

// ฟังก์ชันดูรายละเอียดประวัติการค้นหาแต่ละครั้ง
export const getSearchHistoryDetail = async (req, res) => {
  try {
    // ดึง userId จาก JWT token
    const userId = req.user.userId;
    // รับ historyId จาก URL parameters
    const { historyId } = req.params;

    // ค้นหาประวัติการค้นหาที่ตรงกับ historyId และ userId
    const history = await SearchHistory.findOne({ _id: historyId, userId });

    // ตรวจสอบว่าพบประวัติหรือไม่
    if (!history) {
      return res.status(404).json({ message: 'ไม่พบประวัติการค้นหานี้' });
    }

    // ส่งรายละเอียดประวัติกลับไป (รวม results)
    res.status(200).json(history);

  } catch (error) {
    // แสดง error ใน console
    console.error('Get History Detail Error:', error);
    // ส่ง error response กลับไป
    res.status(500).json({ message: 'เกิดข้อผิดพลาด', error: error.message });
  }
};

// ฟังก์ชันลบประวัติการค้นหา
export const deleteSearchHistory = async (req, res) => {
  try {
    // ดึง userId จาก JWT token
    const userId = req.user.userId;
    // รับ historyId จาก URL parameters
    const { historyId } = req.params;

    // ลบประวัติการค้นหาที่ตรงกับ historyId และ userId
    const result = await SearchHistory.deleteOne({ _id: historyId, userId });

    // ตรวจสอบว่าลบสำเร็จหรือไม่
    if (result.deletedCount === 0) {
      return res.status(404).json({ message: 'ไม่พบประวัติการค้นหานี้' });
    }

    // ส่ง response กลับไปว่าลบสำเร็จ
    res.status(200).json({ message: 'ลบประวัติสำเร็จ' });

  } catch (error) {
    // แสดง error ใน console
    console.error('Delete History Error:', error);
    // ส่ง error response กลับไป
    res.status(500).json({ message: 'เกิดข้อผิดพลาด', error: error.message });
  }
};
