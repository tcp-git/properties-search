// ตัวอย่างการใช้งาน API ด้วย JavaScript
// รันด้วย: node test_client_example.js

const BASE_URL = 'http://localhost:3000';

// ฟังก์ชันสำหรับ Register
async function register(username, email, password) {
  const response = await fetch(`${BASE_URL}/api/auth/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, email, password })
  });
  return await response.json();
}

// ฟังก์ชันสำหรับ Login
async function login(email, password) {
  const response = await fetch(`${BASE_URL}/api/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password })
  });
  return await response.json();
}

// ฟังก์ชันสำหรับดู Profile
async function getProfile(token) {
  const response = await fetch(`${BASE_URL}/api/auth/profile`, {
    headers: { 'Authorization': `Bearer ${token}` }
  });
  return await response.json();
}

// ฟังก์ชันสำหรับค้นหา
async function search(token, query) {
  const response = await fetch(
    `${BASE_URL}/api/search?q=${encodeURIComponent(query)}`,
    {
      headers: { 'Authorization': `Bearer ${token}` }
    }
  );
  return await response.json();
}

// ฟังก์ชันสำหรับดูประวัติการค้นหา
async function getSearchHistory(token, limit = 10, page = 1) {
  const response = await fetch(
    `${BASE_URL}/api/search/history?limit=${limit}&page=${page}`,
    {
      headers: { 'Authorization': `Bearer ${token}` }
    }
  );
  return await response.json();
}

// ฟังก์ชันสำหรับดูรายละเอียดประวัติ
async function getSearchHistoryDetail(token, historyId) {
  const response = await fetch(
    `${BASE_URL}/api/search/history/${historyId}`,
    {
      headers: { 'Authorization': `Bearer ${token}` }
    }
  );
  return await response.json();
}

// ฟังก์ชันสำหรับลบประวัติ
async function deleteSearchHistory(token, historyId) {
  const response = await fetch(
    `${BASE_URL}/api/search/history/${historyId}`,
    {
      method: 'DELETE',
      headers: { 'Authorization': `Bearer ${token}` }
    }
  );
  return await response.json();
}

// ฟังก์ชันหลักสำหรับทดสอบ
async function main() {
  try {
    console.log('🚀 เริ่มทดสอบ API...\n');

    // 1. ลงทะเบียน
    console.log('1️⃣ ลงทะเบียนผู้ใช้ใหม่...');
    const registerResult = await register(
      'testuser_' + Date.now(),
      `test${Date.now()}@example.com`,
      'password123'
    );
    console.log('✅ ลงทะเบียนสำเร็จ:', registerResult);
    console.log('');

    // 2. Login
    console.log('2️⃣ เข้าสู่ระบบ...');
    const loginResult = await login(
      registerResult.email || `test${Date.now()}@example.com`,
      'password123'
    );
    
    if (!loginResult.token) {
      // ถ้า register ไม่สำเร็จ ลอง login ด้วย user เก่า
      const oldLogin = await login('demo@example.com', 'password123');
      if (!oldLogin.token) {
        throw new Error('Login ไม่สำเร็จ');
      }
      loginResult.token = oldLogin.token;
    }
    
    const token = loginResult.token;
    console.log('✅ Login สำเร็จ');
    console.log('Token:', token.substring(0, 20) + '...');
    console.log('');

    // 3. ดู Profile
    console.log('3️⃣ ดูข้อมูล Profile...');
    const profile = await getProfile(token);
    console.log('✅ Profile:', profile);
    console.log('');

    // 4. ค้นหาด้วย AI - ครั้งที่ 1
    console.log('4️⃣ ค้นหาด้วย AI (ครั้งที่ 1)...');
    const searchResult1 = await search(token, 'หาคอนโดใกล้ BTS ราคาไม่เกิน 3 ล้าน');
    console.log('✅ ผลการค้นหา:');
    console.log('  - Query:', searchResult1.query);
    console.log('  - Intent:', searchResult1.intent_detected);
    console.log('  - จำนวนผลลัพธ์:', searchResult1.results?.length || 0);
    console.log('');

    // 5. ค้นหาด้วย AI - ครั้งที่ 2
    console.log('5️⃣ ค้นหาด้วย AI (ครั้งที่ 2)...');
    const searchResult2 = await search(token, 'บ้านเดี่ยว 2 ชั้น มีสระว่ายน้ำ');
    console.log('✅ ผลการค้นหา:');
    console.log('  - Query:', searchResult2.query);
    console.log('  - จำนวนผลลัพธ์:', searchResult2.results?.length || 0);
    console.log('');

    // 6. ดูประวัติการค้นหา
    console.log('6️⃣ ดูประวัติการค้นหา...');
    const history = await getSearchHistory(token, 10, 1);
    console.log('✅ ประวัติการค้นหา:');
    console.log('  - จำนวนทั้งหมด:', history.pagination?.total || 0);
    console.log('  - หน้าปัจจุบัน:', history.pagination?.page || 1);
    
    if (history.history && history.history.length > 0) {
      console.log('  - ประวัติล่าสุด:');
      history.history.slice(0, 3).forEach((item, index) => {
        console.log(`    ${index + 1}. "${item.query}" (${item.resultsCount} results)`);
      });
      
      // 7. ดูรายละเอียดประวัติแรก
      const firstHistoryId = history.history[0]._id;
      console.log('');
      console.log('7️⃣ ดูรายละเอียดประวัติแรก...');
      const historyDetail = await getSearchHistoryDetail(token, firstHistoryId);
      console.log('✅ รายละเอียด:');
      console.log('  - Query:', historyDetail.query);
      console.log('  - Timestamp:', historyDetail.timestamp);
      console.log('  - Results Count:', historyDetail.resultsCount);
    }
    
    console.log('');
    console.log('🎉 ทดสอบเสร็จสมบูรณ์!');

  } catch (error) {
    console.error('❌ เกิดข้อผิดพลาด:', error.message);
    if (error.response) {
      console.error('Response:', await error.response.text());
    }
  }
}

// รันฟังก์ชันหลัก
main();
