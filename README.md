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

1. Clone โปรเจคนี้
```bash
git clone https://github.com/BlamzKunG/BlamzKunG-ChessBot.git
cd BlamzKunG-ChessBot
```
ติดตั้ง dependency
```bash
pip install python-chess
```
ดาวน์โหลด Stockfish binary จาก GitHub:

Windows / Mac / Linux: Stockfish releases

เลือกไฟล์ตาม OS ของคุณ เช่น stockfish_15_x64_avx2.exe สำหรับ Windows

วางไฟล์ .exe (หรือ binary) ในโฟลเดอร์เดียวกับโปรเจค หรือระบุ path ให้ตรงกับ engine.py

🛠️ การใช้งาน
ตัวอย่างเริ่มต้น (start_bot.py)
python
Copy code
import os
from engine import Engine
import chess

# ตั้ง skill ผ่าน environment variable (optional)
os.environ["STOCKFISH_SKILL"] = "5"  # ปานกลาง

# สร้าง engine instance
bot = Engine(path="stockfish.exe")

# เลือก move จาก FEN
fen = chess.STARTING_FEN
move = bot.get_best_move(fen, time_limit=0.1)  # time-based 0.1s
print("Bot move:", move)

# depth-based (ความลึก 6)
move2 = bot.get_best_move(fen, depth=6)
print("Bot move (depth 6):", move2)

bot.close()
เรียกใช้งาน skill-level แบบ runtime
python
Copy code
# เปลี่ยน skill level ขณะรัน
bot.set_skill_level(10)  # จะ clamp สำหรับ Stockfish 0..20
💡 Notes
Skill Level > 20 จะ clamp เป็น 20 สำหรับ Stockfish แต่ค่าที่ผู้ใช้ระบุจะเก็บไว้ใน custom_skill

ถ้าไม่ระบุ skill level ใน constructor หรือ env var → ใช้ default 3

รองรับการเลือก Skill Level ผ่าน start_bot.py menu หรือ environment variable

รองรับการใช้เวลา (time_limit) หรือความลึก (depth) ในการคิดของ engine

📂 โครงสร้างไฟล์
pgsql
Copy code
BlamzKunG-ChessBot/
│
├── engine.py        # wrapper Stockfish engine
├── start_bot.py     # menu เลือก skill level + ASCII art
├── README.md        # ไฟล์นี้
└── stockfish.exe    # ต้องดาวน์โหลดเองจาก link ด้านบน
📝 License
โปรเจคนี้ สามารถใช้งาน, คัดลอก, แก้ไข และนำไปใช้ใน portfolio ได้โดยไม่ต้องขออนุญาต
Stockfish เป็นโปรแกรม GPL v3 license ดูรายละเอียด

🎨 ASCII Art Title
markdown
Copy code
 ________  ___  ___  _______   ________   ________           ________  ________  _________   
|\   ____\|\  \|\  \|\  ___ \ |\   ____\ |\   ____\         |\   __  \|\   __  \|\___   ___\ 
\ \  \___|\ \  \\\  \ \   __/|\ \  \___|_\ \  \___|_        \ \  \|\ /\ \  \|\  \|___ \  \_| 
 \ \  \    \ \   __  \ \  \_|/_\ \_____  \\ \_____  \        \ \   __  \ \  \\\  \   \ \  \  
  \ \  \____\ \  \ \  \ \  \_|\ \|____|\  \\|____|\  \        \ \  \|\  \ \  \\\  \   \ \  \ 
   \ \_______\ \__\ \__\ \_______\____\_\  \ ____\_\  \        \ \_______\ \_______\   \ \__\
    \|_______|\|__|\|__|\|_______|\_________\\_________\        \|_______|\|_______|    \|__|
                                 \|_________\|_________|                                     
✅ สรุป
BlamzKunG Chess Bot คือ Chess AI แบบ customizable ที่ปรับ skill-level, เวลา และความลึกได้เอง เหมาะสำหรับ portfolio, การทดสอบ AI หรือแค่สนุกกับ Chess Engine แบบมืออาชีพ
