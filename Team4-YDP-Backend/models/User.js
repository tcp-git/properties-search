// นำเข้า mongoose สำหรับจัดการ MongoDB
import mongoose from 'mongoose';

// กำหนด Schema สำหรับ User (โครงสร้างข้อมูลผู้ใช้)
const userSchema = new mongoose.Schema({
  // ชื่อผู้ใช้
  username: {
    type: String, // ชนิดข้อมูลเป็น String
    required: [true, 'กรุณาระบุชื่อผู้ใช้'], // จำเป็นต้องมี
    unique: true, // ต้องไม่ซ้ำกัน
    trim: true, // ตัดช่องว่างหน้าหลังออก
    minlength: [3, 'ชื่อผู้ใช้ต้องมีอย่างน้อย 3 ตัวอักษร'] // ความยาวขั้นต่ำ 3 ตัวอักษร
  },

  // อีเมล
  email: {
    type: String, // ชนิดข้อมูลเป็น String
    required: [true, 'กรุณาระบุอีเมล'], // จำเป็นต้องมี
    unique: true, // ต้องไม่ซ้ำกัน
    lowercase: true, // แปลงเป็นตัวพิมพ์เล็กอัตโนมัติ
    trim: true, // ตัดช่องว่างหน้าหลังออก
    match: [/^\S+@\S+\.\S+$/, 'กรุณาระบุอีเมลที่ถูกต้อง'] // ตรวจสอบรูปแบบอีเมล
  },

  // รหัสผ่าน (จะถูกเข้ารหัสด้วย bcrypt ก่อนบันทึก)
  password: {
    type: String, // ชนิดข้อมูลเป็น String
    required: [true, 'กรุณาระบุรหัสผ่าน'], // จำเป็นต้องมี
    minlength: [6, 'รหัสผ่านต้องมีอย่างน้อย 6 ตัวอักษร'] // ความยาวขั้นต่ำ 6 ตัวอักษร
  },

  // วันที่สร้างบัญชี
  createdAt: {
    type: Date, // ชนิดข้อมูลเป็น Date
    default: Date.now // ค่าเริ่มต้นเป็นเวลาปัจจุบัน
  }
});

// สร้าง Model จาก Schema
const User = mongoose.model('User', userSchema);

// ส่งออก Model เพื่อใช้ในส่วนอื่น
export default User;
