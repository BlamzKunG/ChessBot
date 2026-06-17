# Token ของ bot
TOKEN = "token"
POLL_INTERVAL = 1
# รูปแบบเกม (สำหรับตอนทดสอบเราใช้ 'unlimited')
# Lichess API จะส่ง challenge มาแล้ว bot จะตอบรับอัตโนมัติ
GAME_VARIANT = "unlimited"  # ไม่จำกัดเวลา, casual

# --- Engine & Time Management ---
STOCKFISH_PATH = "stockfish" # หรือ "stockfish.exe"
MOVE_OVERHEAD = 500  # ms (หักลบเวลาเพื่อกันเวลาหมดเพราะเน็ตช้า)
MIN_TIME = 0.05      # วินาทีขั้นต่ำต่อตา (ปรับลดลงเพื่อ Ultra Speed)
MAX_TIME = 20.0      # วินาทีสูงสุดต่อตา (เพิ่มขึ้นเพื่อกรณีเสียเปรียบหนัก)
DEFAULT_DEPTH = 15   # Depth พื้นฐานถ้าไม่ใช้เวลา


