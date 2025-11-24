// นำเข้า Express framework
import express from 'express';
// นำเข้า search controller ที่มีฟังก์ชันจัดการการค้นหา
import * as searchController from '../controllers/searchController.js';
// นำเข้า middleware สำหรับตรวจสอบ JWT token
import * as authMiddleware from '../middleware/authMiddleware.js';

// สร้าง router สำหรับจัดการ routes
const router = express.Router();

// Route สำหรับค้นหาด้วย AI (ต้อง login ก่อน)
// GET /api/search?q=keyword&filters={}
// ใช้ verifyToken middleware เพื่อตรวจสอบ JWT token ก่อนค้นหา
router.get('/', authMiddleware.verifyToken, searchController.search);

// Route สำหรับดูประวัติการค้นหา (ต้อง login ก่อน)
// GET /api/search/history?limit=20&page=1
// รองรับ pagination ด้วย limit และ page
router.get('/history', authMiddleware.verifyToken, searchController.getSearchHistory);

// Route สำหรับดูรายละเอียดประวัติการค้นหาแต่ละครั้ง (ต้อง login ก่อน)
// GET /api/search/history/:historyId
// historyId คือ ID ของประวัติการค้นหาที่ต้องการดู
router.get('/history/:historyId', authMiddleware.verifyToken, searchController.getSearchHistoryDetail);

// Route สำหรับลบประวัติการค้นหา (ต้อง login ก่อน)
// DELETE /api/search/history/:historyId
// historyId คือ ID ของประวัติการค้นหาที่ต้องการลบ
router.delete('/history/:historyId', authMiddleware.verifyToken, searchController.deleteSearchHistory);

// ส่งออก router เพื่อใช้ใน index.js
export default router;
