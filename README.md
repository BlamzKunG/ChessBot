# BlamzKunG

BlamzKunG เป็น Chess Bot ที่ใช้ Stockfish เป็น Engine หลัก โดยออกแบบให้สามารถปรับ **Skill Level**, **Depth**, และ **Time Limit** ในการคิดของบอทได้อย่างยืดหยุ่น พร้อมรองรับการใช้งานแบบ time-based หรือ depth-based search  

Bot นี้ถูกสร้างขึ้นเพื่อเรียนรู้การสร้าง Chess AI แบบง่ายต่อการปรับแต่ง และสามารถนำไปต่อยอดในโปรเจคของตัวเองได้

---

## คุณสมบัติหลัก

- ใช้งานง่าย ผ่าน Python wrapper `engine.py`
- เลือกระดับของบอทได้ เช่น:
  - บอทเร็ว: skill level 1
  - บอทปานกลาง: skill level 5
  - บอทเก่ง: skill level 20
  - บอทโครตเทพ: skill level 100 (แต่ Stockfish จะ clamp ที่ 20)
  - บอท Custom: ระบุ Skill Level เอง
- รองรับ **time-based thinking** และ **depth-based thinking**
- ใช้ **Single Engine Process** เพื่อประสิทธิภาพสูง
- รองรับการปรับ **Threads** และ **Hash Size** ของ Stockfish

---

## เริ่มใช้งาน

1. ดาวน์โหลด Stockfish จาก GitHub (เลือกเวอร์ชันที่ตรงกับ OS ของคุณ):  
[https://github.com/official-stockfish/Stockfish](https://github.com/official-stockfish/Stockfish)

2. วางไฟล์ `stockfish.exe` หรือ binary ลงในโฟลเดอร์เดียวกับโปรเจค

3. ติดตั้ง dependencies:

```bash
pip install python-chess

4. เลือกระดับของบอทผ่านไฟล์ start_bot.py:



python start_bot.py

เลือกระดับของบอทตาม prompt

หรือเลือก Custom แล้วใส่ Skill Level ที่ต้องการ


5. ใช้งาน Engine ในโค้ด Python:



from engine import Engine

bot = Engine(path="stockfish.exe")  # จะอ่าน skill จาก start_bot.py หรือ env variable
fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
move = bot.get_best_move(fen, time_limit=0.05)  # คิด 50ms
print("Bot move:", move)
bot.close()


---

โครงสร้างโปรเจค

BlamzKunG/
├── engine.py          # Chess Engine wrapper
├── start_bot.py       # CLI สำหรับเลือก Skill Level
├── README.md          # ไฟล์นี้
└── stockfish.exe      # Stockfish binary (ดาวน์โหลดเอง)


---

Notes

Stockfish Skill Level UCI ปกติรองรับ 0–20 หากใส่ค่าเกินจะถูก clamp เป็น 20

สามารถปรับ Threads และ Hash ใน Engine เพื่อเพิ่ม performance

สามารถนำโค้ดนี้ไปต่อยอดเป็น Bot Online หรือวิเคราะห์เกม Chess ในโปรเจคอื่น ๆ ได้



---

License
