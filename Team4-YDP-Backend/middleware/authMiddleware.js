// นำเข้า jsonwebtoken สำหรับตรวจสอบ JWT token
import jwt from 'jsonwebtoken';

// Middleware สำหรับตรวจสอบ JWT token
export const verifyToken = (req, res, next) => {
  try {
    // รับ token จาก Authorization header
    // Format: "Bearer TOKEN" จึงต้อง split และเอาตัวที่ 2
    const token = req.headers.authorization?.split(' ')[1];

    // ตรวจสอบว่ามี token หรือไม่
    if (!token) {
      return res.status(401).json({ message: 'ไม่พบ token กรุณา login' });
    }

    // ตรวจสอบความถูกต้องของ token ด้วย JWT_SECRET
    const decoded = jwt.verify(token, process.env.JWT_SECRET);

    // เก็บข้อมูลผู้ใช้ที่ decode จาก token ไว้ใน req.user
    // decoded จะมีข้อมูล: { userId, email, username, iat, exp }
    req.user = decoded;

    // ส่งต่อไปยัง controller ถัดไป
    next();

  } catch (error) {
    // จัดการ error ต่างๆ ที่อาจเกิดขึ้น
    if (error.name === 'JsonWebTokenError') {
      // token ไม่ถูกต้อง (เช่น ถูกแก้ไข)
      return res.status(401).json({ message: 'Token ไม่ถูกต้อง' });
    }
    if (error.name === 'TokenExpiredError') {
      // token หมดอายุ
      return res.status(401).json({ message: 'Token หมดอายุ' });
    }
    // error อื่นๆ
    return res.status(500).json({ message: 'เกิดข้อผิดพลาด', error: error.message });
  }
};
