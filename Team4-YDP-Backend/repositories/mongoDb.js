import { MongoClient, ServerApiVersion } from 'mongodb';
import 'dotenv/config';

// ใช้ URI จาก environment variable เหมือนกับส่วนอื่นของโปรเจกต์
const uri = process.env.MONGODB_URI || "mongodb+srv://webdev:webdev123@cluster0.s5i1jtq.mongodb.net/ai-property-search?retryWrites=true&w=majority";

// Create a MongoClient with a MongoClientOptions object to set the Stable API version
const client = new MongoClient(uri, {
  serverApi: {
    version: ServerApiVersion.v1,
    strict: true,
    deprecationErrors: true,
  },
  serverSelectionTimeoutMS: 5000,
  socketTimeoutMS: 45000,
});

async function getUsers() {
  try {
    await client.connect();
    const database = client.db('Moki');
    const users = database.collection('Users');
    const results = await users.find({}).toArray();
    return results;
  } catch (error) {
    console.error("เกิดข้อผิดพลาดในการดึงข้อมูลผู้ใช้:", error);
    throw error;
  } finally {
    await client.close();
  }
}

async function createUsers(name, age, likes) {
  try {
    await client.connect();
    const database = client.db('Moki')
    const users = database.collection('Users')
    const result = await users.insertOne({ "name": name, "age": age, "likes": likes });
    return result;
  } catch (error) {
    console.error("เกิดข้อผิดพลาดในการสร้างผู้ใช้:", error);
    throw error;
  }
}

async function deleteUsers(userId) {
  try {
    await client.connect();
    const database = client.db('Moki')
    const users = database.collection('Users')
    const result = await users.deleteOne({ "name": userId });
    return result;
  } catch (error) {
    console.error("เกิดข้อผิดพลาดในการลบผู้ใช้:", error);
    throw error;
  }
}


export { getUsers, createUsers, deleteUsers };
