// นำเข้า Express framework
import express from 'express';
// นำเข้า auth controller ที่มีฟังก์ชันจัดการ authentication
import * as authController from '../controllers/authController.js';
// นำเข้า middleware สำหรับตรวจสอบ JWT token
import * as authMiddleware from '../middleware/authMiddleware.js';

// สร้าง router สำหรับจัดการ routes
const router = express.Router();

// Route สำหรับลงทะเบียนผู้ใช้ใหม่
// POST /api/auth/register
router.post('/register', authController.register);

// Route สำหรับเข้าสู่ระบบ (ได้ JWT token)
// POST /api/auth/login
router.post('/login', authController.login);

// Route สำหรับออกจากระบบ
// POST /api/auth/logout
router.post('/logout', authController.logout);

// Route สำหรับดูข้อมูล profile (ต้อง login ก่อน)
// GET /api/auth/profile
// ใช้ verifyToken middleware เพื่อตรวจสอบ JWT token ก่อนเข้าถึง controller
router.get('/profile', authMiddleware.verifyToken, authController.getProfile);

// ส่งออก router เพื่อใช้ใน index.js
export default router;
