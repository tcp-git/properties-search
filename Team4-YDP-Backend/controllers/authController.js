// นำเข้า User model สำหรับจัดการข้อมูลผู้ใช้
import User from '../models/User.js';
// นำเข้า bcrypt สำหรับเข้ารหัสรหัสผ่าน
import bcrypt from 'bcrypt';
// นำเข้า jsonwebtoken สำหรับสร้าง JWT token
import jwt from 'jsonwebtoken';

// ฟังก์ชันสำหรับลงทะเบียนผู้ใช้ใหม่
export const register = async (req, res) => {
  try {
    // รับข้อมูล username, email, password จาก request body
    const { username, email, password } = req.body;

    // ตรวจสอบว่ามีข้อมูลครบถ้วนหรือไม่
    if (!username || !email || !password) {
      return res.status(400).json({ message: 'กรุณาระบุชื่อผู้ใช้ อีเมล และรหัสผ่าน' });
    }

    // ตรวจสอบว่า email หรือ username ซ้ำในระบบหรือไม่
    const existingUser = await User.findOne({ $or: [{ email }, { username }] });
    if (existingUser) {
      return res.status(400).json({ message: 'ชื่อผู้ใช้หรืออีเมลนี้มีอยู่ในระบบแล้ว' });
    }

    // เข้ารหัส password ด้วย bcrypt (10 rounds)
    const hashedPassword = await bcrypt.hash(password, 10);

    // สร้างผู้ใช้ใหม่ในฐานข้อมูล
    const newUser = new User({
      username,
      email,
      password: hashedPassword
    });
    // บันทึกลงฐานข้อมูล
    await newUser.save();

    // ส่ง response กลับไปว่าสำเร็จพร้อม userId
    res.status(201).json({ message: 'ลงทะเบียนสำเร็จ', userId: newUser._id });

  } catch (error) {
    // แสดง error ใน console
    console.error('Register Error:', error);
    // ส่ง error response กลับไป
    res.status(500).json({ message: 'เกิดข้อผิดพลาดในการลงทะเบียน', error: error.message });
  }
};

// ฟังก์ชันสำหรับเข้าสู่ระบบ
export const login = async (req, res) => {
  try {
    // รับข้อมูล email และ password จาก request body
    const { email, password } = req.body;

    // ตรวจสอบว่ามีข้อมูลครบถ้วนหรือไม่
    if (!email || !password) {
      return res.status(400).json({ message: 'กรุณาระบุอีเมลและรหัสผ่าน' });
    }

    // ค้นหาผู้ใช้จากฐานข้อมูลด้วย email
    const user = await User.findOne({ email });

    // ตรวจสอบว่าพบผู้ใช้หรือไม่
    if (!user) {
      return res.status(401).json({ message: 'อีเมลหรือรหัสผ่านไม่ถูกต้อง' });
    }

    // เปรียบเทียบ password ที่ส่งมากับ password ที่เข้ารหัสในฐานข้อมูล
    const isPasswordValid = await bcrypt.compare(password, user.password);
    if (!isPasswordValid) {
      return res.status(401).json({ message: 'อีเมลหรือรหัสผ่านไม่ถูกต้อง' });
    }

    // สร้าง JWT token โดยใส่ข้อมูล userId, email, username
    const token = jwt.sign(
      { userId: user._id, email: user.email, username: user.username },
      process.env.JWT_SECRET, // ใช้ secret key จาก environment variable
      { expiresIn: '24h' } // token หมดอายุใน 24 ชั่วโมง
    );

    // ส่ง token และข้อมูลผู้ใช้กลับไป
    res.status(200).json({
      message: 'เข้าสู่ระบบสำเร็จ',
      token: token,
      user: { id: user._id, username: user.username, email: user.email }
    });

  } catch (error) {
    // แสดง error ใน console
    console.error('Login Error:', error);
    // ส่ง error response กลับไป
    res.status(500).json({ message: 'เกิดข้อผิดพลาดในการเข้าสู่ระบบ', error: error.message });
  }
};

// ฟังก์ชันสำหรับออกจากระบบ
export const logout = async (req, res) => {
  try {
    // สำหรับ JWT token การ logout จะทำที่ฝั่ง client โดยการลบ token
    // ส่ง response กลับไปว่า logout สำเร็จ
    res.status(200).json({ message: 'ออกจากระบบสำเร็จ' });

  } catch (error) {
    // ส่ง error response กลับไป
    res.status(500).json({ message: 'เกิดข้อผิดพลาด', error: error.message });
  }
};

// ฟังก์ชันสำหรับดูข้อมูล profile ของผู้ใช้
export const getProfile = async (req, res) => {
  try {
    // ดึง userId จาก JWT token ที่ถูก decode โดย middleware
    const userId = req.user.userId;

    // ค้นหาผู้ใช้จากฐานข้อมูลโดยไม่เอา password มาด้วย
    const user = await User.findById(userId).select('-password');

    // ตรวจสอบว่าพบผู้ใช้หรือไม่
    if (!user) {
      return res.status(404).json({ message: 'ไม่พบข้อมูลผู้ใช้' });
    }

    // ส่งข้อมูลผู้ใช้กลับไป
    res.status(200).json({ user });

  } catch (error) {
    // แสดง error ใน console
    console.error('Get Profile Error:', error);
    // ส่ง error response กลับไป
    res.status(500).json({ message: 'เกิดข้อผิดพลาด', error: error.message });
  }
};
