// นำเข้า mongoose สำหรับจัดการ MongoDB
import mongoose from 'mongoose';

// กำหนด Schema สำหรับ SearchHistory
const searchHistorySchema = new mongoose.Schema({
    // ID ของผู้ใช้ที่ทำการค้นหา (อ้างอิงจาก User model)
    userId: {
        type: mongoose.Schema.Types.ObjectId,
        ref: 'User', // อ้างอิงไปที่ User collection
        required: true // จำเป็นต้องมี
    },
    // คำค้นหาที่ผู้ใช้ป้อน
    query: {
        type: String,
        required: true, // จำเป็นต้องมี
        trim: true // ตัดช่องว่างหน้าหลังออก
    },
    // filters เพิ่มเติมที่ใช้ในการค้นหา (เช่น ราคา, ที่ตั้ง)
    filters: {
        type: Object,
        default: {} // ค่าเริ่มต้นเป็น object ว่าง
    },
    // intent ที่ AI ตรวจจับได้จากคำค้นหา
    intentDetected: {
        type: Object,
        default: {} // ค่าเริ่มต้นเป็น object ว่าง
    },
    // จำนวนผลลัพธ์ที่ได้จากการค้นหา
    resultsCount: {
        type: Number,
        default: 0 // ค่าเริ่มต้นเป็น 0
    },
    // ผลลัพธ์ทั้งหมดจากการค้นหา
    results: {
        type: Array,
        default: [] // ค่าเริ่มต้นเป็น array ว่าง
    },
    // เวลาที่ทำการค้นหา
    timestamp: {
        type: Date,
        default: Date.now // ค่าเริ่มต้นเป็นเวลาปัจจุบัน
    }
});

// สร้าง index สำหรับเพิ่มประสิทธิภาพการค้นหาประวัติของแต่ละ user
// เรียงตาม userId และ timestamp (จากใหม่ไปเก่า)
searchHistorySchema.index({ userId: 1, timestamp: -1 });

// สร้าง Model จาก Schema
const SearchHistory = mongoose.model('SearchHistory', searchHistorySchema);

// ส่งออก Model เพื่อใช้ในส่วนอื่น
export default SearchHistory;
