import mongoose from 'mongoose';

const connectDB = async () => {
    try {
        const uri = process.env.MONGODB_URI || "mongodb+srv://webdev:webdev123@cluster0.s5i1jtq.mongodb.net/ai-property-search?retryWrites=true&w=majority";
        
        const conn = await mongoose.connect(uri, {
            serverSelectionTimeoutMS: 5000,
            socketTimeoutMS: 45000,
        });
        
        console.log(`MongoDB Connected: ${conn.connection.host}`);
    } catch (error) {
        console.error(`MongoDB Connection Error: ${error.message}`);
        console.error('กรุณาตรวจสอบ:');
        console.error('1. MONGODB_URI ใน .env ถูกต้อง');
        console.error('2. IP Address ของคุณได้รับอนุญาตใน MongoDB Atlas');
        console.error('3. Username/Password ถูกต้อง');
        // ไม่ exit เพื่อให้ server ยังทำงานต่อได้
        // process.exit(1);
    }
};

export default connectDB;
