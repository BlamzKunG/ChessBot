\<div align="center"\>

# BlamzKunG Chess Bot ♟️

**บอทหมากรุกขุมพลัง Stockfish ที่ปรับแต่งได้ตามใจนึก เหมาะสำหรับทดสอบกลยุทธ์, เล่นสนุก หรือสร้าง Portfolio สุดเจ๋งของคุณ**

\</div\>

\<p align="center"\>
\<img alt="Python Version" src="[https://img.shields.io/badge/Python-3.10%2B-blue?logo=python\&logoColor=yellow](https://www.google.com/search?q=https://img.shields.io/badge/Python-3.10%252B-blue%3Flogo%3Dpython%26logoColor%3Dyellow)"\>
\<img alt="License" src="[https://img.shields.io/badge/License-MIT-green.svg](https://www.google.com/search?q=https://img.shields.io/badge/License-MIT-green.svg)"\>
\<img alt="Powered by" src="[https://img.shields.io/badge/Powered%20by-Stockfish-orange](https://www.google.com/search?q=https://img.shields.io/badge/Powered%2520by-Stockfish-orange)"\>
\</p\>

-----

**BlamzKunG Chess Bot** คือ Chess Bot ที่ใช้ Stockfish ซึ่งเป็นหนึ่งใน Chess Engine ที่แข็งแกร่งที่สุดในโลกเป็น Backend จุดเด่นของโปรเจกต์นี้คือความสามารถในการปรับแต่ง **Skill Level และเวลาคิด** ของบอทได้อย่างอิสระ ทำให้คุณสามารถสร้างคู่ต่อสู้ที่เหมาะสมกับระดับฝีมือของคุณ หรือจะใช้เพื่อทดสอบ AI ปะทะ AI สำหรับ Portfolio ของนักพัฒนาเกม, AI, หรือนักพัฒนาระบบ Trading ก็ได้เช่นกัน

## 🎯 คุณสมบัติเด่น (Key Features)

  - **ขุมพลัง Stockfish**: ขับเคลื่อนด้วย Stockfish (UCI) chess engine ที่มีชื่อเสียงระดับโลก
  - **ปรับ Skill Level ได้หลากหลาย**:
      - `ระดับเริ่มต้น`: Skill Level 1
      - `ระดับกลาง`: Skill Level 5
      - `ระดับสูง`: Skill Level 20
      - `ระดับเทพ`: Skill Level 100+
      - `กำหนดเอง`: ตั้งค่า Skill Level ได้ตามต้องการ
  - **ควบคุมการค้นหาที่ยืดหยุ่น**: รองรับทั้งการค้นหาตาม **เวลา (Time-based)** และ **ความลึก (Depth-based)**
  - **ปรับแต่ง Performance**: สามารถกำหนดจำนวน Threads และขนาดของ Hash Table เพื่อรีดประสิทธิภาพสูงสุด
  - **Real-time Skill Update**: เปลี่ยน Skill Level ของบอทได้ทันทีผ่าน Environment Variable (`STOCKFISH_SKILL`) โดยไม่ต้องรีสตาร์ท
  - **ใช้งานง่าย**: มาพร้อม Python API ที่เรียบง่ายและเข้าใจง่าย
  - **Cross-Platform**: ทำงานได้บน Windows, Linux, และ macOS (ต้องการ Python 3.10 ขึ้นไป)

## 🚀 เริ่มต้นใช้งาน (Getting Started)

### 1\. Clone โปรเจกต์

```bash
git clone https://github.com/BlamzKunG/BlamzKunG-ChessBot.git
cd BlamzKunG-ChessBot
```

### 2\. ติดตั้ง Dependencies

ติดตั้ง Library ที่จำเป็นทั้งหมดด้วยคำสั่งเดียว:

```bash
pip install berserk python-chess requests
```

### 3\. ดาวน์โหลด Stockfish Engine

> **สำคัญมาก:** โปรเจกต์นี้ไม่ได้รวมไฟล์ Stockfish มาให้ คุณต้องดาวน์โหลดเอง

1.  ไปที่หน้า [Stockfish Downloads](https://stockfishchess.org/download/)
2.  เลือกเวอร์ชันที่ตรงกับระบบปฏิบัติการของคุณ (เช่น `stockfish_15_x64_avx2.exe` สำหรับ Windows)
3.  นำไฟล์ Binary ที่ดาวน์โหลดมา (เช่น `stockfish.exe`) **วางไว้ในโฟลเดอร์หลักของโปรเจกต์** (ที่เดียวกับไฟล์ `engine.py`)

### 4\. รันบอท\!

เปิดเมนูเพื่อเลือกระดับความสามารถของบอทและเริ่มทำงาน:

```bash
python start_bot.py
```

## 📂 โครงสร้างโปรเจกต์

```bash
BlamzKunG-ChessBot/
├── Bot.py           # โค้ดหลักในการเชื่อมต่อและเล่นบน Lichess
├── engine.py        # ตัวกลางสำหรับสื่อสารกับ Stockfish Engine
├── start_bot.py     # สคริปต์เริ่มต้น พร้อมเมนูเลือก Skill Level
├── README.md        # ไฟล์ที่คุณกำลังอ่าน
└── stockfish.exe    # (ต้องดาวน์โหลดเอง) ตัว Chess Engine หลัก
```

## ⚙️ การปรับแต่งขั้นสูง

คุณสามารถปรับแต่งค่าต่างๆ ของ Stockfish ได้โดยตรงในไฟล์ `engine.py` เช่น:

  - `"Threads"`: จำนวน CPU threads ที่จะใช้
  - `"Hash"`: ขนาด Memory (MB) สำหรับ Hash Table
  - `"UCI_LimitStrength"` และ `"UCI_Elo"`: สำหรับการจำกัดความสามารถบอทตาม Elo rating

## 📝 สิทธิ์การใช้งาน (License)

  - **BlamzKunG Chess Bot**: โปรเจกต์นี้เปิดให้ใช้งาน, คัดลอก, แก้ไข และนำไปใช้ใน Portfolio ได้อย่างอิสระโดยไม่ต้องขออนุญาต (MIT License)
  - **Stockfish**: เป็นโปรแกรมที่เผยแพร่ภายใต้สัญญาอนุญาตแบบ [GNU General Public License v3.0](https://www.gnu.org/licenses/gpl-3.0.en.html)
