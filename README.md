# BlamzKunG Lichess Chess Bot ♟️

[](https://www.python.org/downloads/)
[](https://opensource.org/licenses/MIT)
[](https://lichess.org/api)

**BlamzKunG Chess Bot** คือ Chess Bot ประสิทธิภาพสูงสำหรับ Lichess ที่ขับเคลื่อนด้วย Stockfish engine ถูกออกแบบมาให้ปรับแต่งได้อย่างยืดหยุ่น เหมาะสำหรับผู้ที่ต้องการคู่ซ้อมหมากรุกที่ปรับระดับความสามารถได้ หรือสำหรับนักพัฒนาที่ต้องการทดสอบตรรกะ AI และสร้าง Portfolio

บอทนี้เชื่อมต่อกับ Lichess ผ่าน API และสามารถรับคำท้าเล่นเกมได้โดยอัตโนมัติ

-----

## 🎯 คุณสมบัติหลัก (Key Features)

  - **🧠 ขับเคลื่อนด้วย Stockfish:** ใช้ Stockfish ซึ่งเป็นหนึ่งใน UCI chess engine ที่แข็งแกร่งที่สุดในโลก
  - **🔧 ปรับระดับความสามารถได้ (Skill Level):**
      - **Beginner:** Skill Level 1
      - **Intermediate:** Skill Level 5
      - **Advanced:** Skill Level 20
      - **God Mode:** Skill Level 100+
      - **Custom:** กำหนดค่าเองได้อย่างอิสระ
  - **⚙️ ควบคุมการค้นหาเชิงลึก:** รองรับการค้นหาทั้งแบบ **Time-based** (กำหนดเวลาคิดต่อตา) และ **Depth-based** (กำหนดความลึกในการค้นหา)
  - **🚀 ปรับแต่งประสิทธิภาพ:** สามารถกำหนดจำนวน Threads และขนาดของ Hash Table เพื่อรีดประสิทธิภาพสูงสุดจากฮาร์ดแวร์ของคุณ
  - **🔄 อัปเดต Skill แบบ Real-time:** สามารถเปลี่ยน Skill Level ของบอทได้ทันทีผ่าน Environment Variable (`STOCKFISH_SKILL`) โดยไม่ต้องรีสตาร์ทบอท
  - **🐍 API ใช้งานง่าย:** เขียนด้วย Python และมีโครงสร้างที่เข้าใจง่าย
  - **💻 รองรับหลายแพลตฟอร์ม:** ทำงานได้บน Windows, Linux, และ macOS

-----

## 🏁 การติดตั้งและใช้งาน (Getting Started)

ทำตามขั้นตอนต่อไปนี้เพื่อติดตั้งและรันบอทของคุณ

### 1\. สิ่งที่ต้องมี (Prerequisites)

  - [Python 3.10+](https://www.python.org/downloads/)
  - [Git](https://git-scm.com/downloads)

### 2\. ขั้นตอนการติดตั้ง (Installation)

**1. Clone โปรเจคนี้**

```bash
git clone https://github.com/BlamzKunG/BlamzKunG-ChessBot.git
cd BlamzKunG-ChessBot
```

**2. ติดตั้ง Libraries ที่จำเป็น**

```bash
pip install berserk python-chess requests
```

*(แนะนำ: สร้าง virtual environment ก่อนเพื่อความสะอาดของโปรเจค)*

**3. ดาวน์โหลด Stockfish Engine**

  - ไปที่หน้า [Stockfish Downloads](https://stockfishchess.org/download/)
  - ดาวน์โหลดเวอร์ชันล่าสุดที่เหมาะกับระบบปฏิบัติการและสถาปัตยกรรม CPU ของคุณ (เช่น `stockfish-windows-x86-64-avx2.exe` สำหรับ Windows)
  - **นำไฟล์ที่ดาวน์โหลดมาวางไว้ในโฟลเดอร์โปรเจค** และเปลี่ยนชื่อเป็น `stockfish.exe` (สำหรับ Windows) หรือ `stockfish` (สำหรับ Linux/macOS) หรือจะระบุ path ของ engine ในไฟล์ `engine.py` ก็ได้

### 3\. การตั้งค่า (Configuration)

**1. สร้าง Lichess API Token**

  - ล็อกอินเข้าสู่ [Lichess.org](https://lichess.org)
  - ไปที่ [Preferences -\> API access tokens](https://lichess.org/account/oauth/token)
  - สร้าง Token ใหม่โดยเลือก Scopes (สิทธิ์) ดังนี้:
      - `[x] Play games with the bot API`
      - `[x] Read incoming challenges`
  - คัดลอก Token ที่ได้เก็บไว้ให้ดี

**2. ตั้งค่า Environment Variable**
บอทจะอ่านค่า Token จาก Environment Variable ที่ชื่อว่า `LICHESS_TOKEN`

**สำหรับ Windows (Command Prompt):**

```cmd
set LICHESS_TOKEN="YOUR_API_TOKEN_HERE"
```

**สำหรับ Linux / macOS:**

```bash
export LICHESS_TOKEN="YOUR_API_TOKEN_HERE"
```

*คุณอาจจะต้องใส่คำสั่งนี้ในไฟล์ `.bashrc` หรือ `.zshrc` เพื่อให้มีผลถาวร*

### 4\. รันบอท (Usage)

หลังจากตั้งค่า Token เรียบร้อยแล้ว สั่งรันบอทได้เลย:

```bash
python start_bot.py
```

เมื่อรันแล้วจะมีเมนูให้เลือกระดับความสามารถเริ่มต้นของบอท บอทจะออนไลน์บน Lichess และพร้อมรับคำท้า\!

-----

## 📂 โครงสร้างไฟล์ (Project Structure)

```
BlamzKunG-ChessBot/
│
├── start_bot.py     # ไฟล์สำหรับรันบอท พร้อมเมนูเลือก Skill Level
├── bot.py           # โค้ดหลักในการเชื่อมต่อกับ Lichess และจัดการเกม
├── engine.py        # Wrapper สำหรับสื่อสารกับ Stockfish engine
├── README.md        # ไฟล์ที่คุณกำลังอ่าน
└── stockfish.exe    # Stockfish binary (ต้องดาวน์โหลดเอง)
```

-----

## 📄 License

โปรเจคนี้อยู่ภายใต้ **MIT License** ซึ่งหมายความว่าคุณสามารถใช้งาน, คัดลอก, แก้ไข

สำหรับ **Stockfish engine** นั้นอยู่ภายใต้ **GPLv3 license** สามารถดูรายละเอียดเพิ่มเติมได้ที่ [เว็บไซต์ของ Stockfish](https://www.google.com/search?q=https://stockfishchess.org/get-stockfish/)

  - ขอขอบคุณทีมผู้พัฒนา **Stockfish** สำหรับ Chess Engine ที่สุดยอด
  - ขอขอบคุณไลบรารี **python-chess** และ **berserk** ที่ทำให้การพัฒนาบอทสำหรับ Lichess เป็นเรื่องง่าย
