# BlamzKunG Chess Bot ♟️

BlamzKunG เป็น **Chess Bot** ที่ใช้ Stockfish เป็น engine backend แต่คุณสามารถปรับ **skill level และเวลาคิด** ของบอทได้อย่างอิสระ เหมาะสำหรับเล่นเองหรือทดสอบ AI vs AI สำหรับ portfolio ของนักพัฒนาเกม/AI/Trading logic

---

## 🎯 คุณสมบัติหลัก

- ใช้ Stockfish (UCI) เป็น engine
- ปรับ Skill Level ของบอทได้
  - บอทเร็ว → skill level 1
  - บอทปานกลาง → skill level 5
  - บอทเก่ง → skill level 20
  - บอทโครตเทพ → skill level 100
  - Custom → กำหนดค่าเองได้
- รองรับทั้ง **time-based** และ **depth-based** search
- สามารถเลือกจำนวน Threads และขนาด Hash ได้
- Realtime skill-level update ผ่าน environment variable (`STOCKFISH_SKILL`)
- ใช้งานง่ายด้วย Python API
- ทำงานบน Windows / Linux / macOS (ต้องมี Python 3.10+)

---

## ⚡ การติดตั้ง

**1. Clone โปรเจคนี้**
```bash
git clone https://github.com/BlamzKunG/BlamzKunG-ChessBot.git
cd BlamzKunG-ChessBot
```
**2.ติดตั้ง Libraries / Packages**
```bash
pip install berserk
pip install python-chess
pip install requests
```
ดาวน์โหลด Stockfish binary จาก GitHub:

Windows / Mac / Linux: Stockfish releases

เลือกไฟล์ตาม OS ของคุณ เช่น stockfish_15_x64_avx2.exe สำหรับ Windows

วางไฟล์ .exe (หรือ binary) ในโฟลเดอร์เดียวกับโปรเจค หรือระบุ path ให้ตรงกับ engine.py


 **3.ใช้งาน**
```bash
python start.py
```

📂 โครงสร้างไฟล์
```pgsql
BlamzKunG-ChessBot/
│
├── Bot.py           # ไฟล์ main
├── engine.py        # wrapper Stockfish engine
├── start_bot.py     # menu เลือก skill level + ASCII art
├── README.md        # ไฟล์นี้
└── stockfish.exe    # ต้องดาวน์โหลดเองจาก link ด้านบน
```

✅ สรุป
BlamzKunG Chess Bot คือ Chess AI แบบ customizable ที่ปรับ skill-level, เวลา และความลึกได้เอง

# License
โปรเจคนี้ สามารถใช้งาน, คัดลอก, แก้ไข ได้โดยไม่ต้องขออนุญาต
Stockfish เป็นโปรแกรม GPL v3 license ดูรายละเอียด
