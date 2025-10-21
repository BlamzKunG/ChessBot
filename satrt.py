from __future__ import annotations
import os
import sys
import subprocess
from typing import Optional

ASCII_TITLE = r"""
 ________  ___  ___  _______   ________   ________           ________  ________  _________   
|\   ____\|\  \|\  \|\  ___ \ |\   ____\ |\   ____\         |\   __  \|\   __  \|\___   ___\ 
\ \  \___|\ \  \\\  \ \   __/|\ \  \___|_\ \  \___|_        \ \  \|\ /\ \  \|\  \|___ \  \_| 
 \ \  \    \ \   __  \ \  \_|/_\ \_____  \\ \_____  \        \ \   __  \ \  \\\  \   \ \  \  
  \ \  \____\ \  \ \  \ \  \_|\ \|____|\  \\|____|\  \        \ \  \|\  \ \  \\\  \   \ \  \ 
   \ \_______\ \__\ \__\ \_______\____\_\  \ ____\_\  \        \ \_______\ \_______\   \ \__\
    \|_______|\|__|\|__|\|_______|\_________\\_________\        \|_______|\|_______|    \|__|
                                 \|_________\|_________|                                     
"""

MENU = [
    ("บอทเร็ว", "fast"),
    ("บอทปานกลาง", "medium"),
    ("บอทเก่ง", "strong"),
    ("บอทโครตเทพ", "godlike"),
    ("บอท Custom (ใส่ Level เอง)", "custom"),
    ("ยกเลิก", "cancel"),
]


# Mapping internal (hidden) — **ไม่แสดงตัวเลขให้ผู้ใช้เห็นในเมนู**
_SKILL_MAPPING = {
    "fast": 1,
    "medium": 5,
    "strong": 20,
    "godlike": 100,  # ผู้ใช้ขอ 100 แต่ Stockfish 'Skill Level' ปกติ 0..20 — อาจถูก engine ignore
}


def clear_screen() -> None:
    # cross-platform clear
    if os.name == "nt":
        os.system("cls")
    else:
        os.system("clear")


def prompt_choice() -> Optional[int]:
    """Show menu (no numeric levels) and return chosen skill (int) or None if cancel."""
    print(ASCII_TITLE)
    print("เลือกระดับของบอท (เลือกเลข):\n")
    for idx, (label, _) in enumerate(MENU, start=1):
        print(f"  {idx}. {label}")
    print()

    try:
        raw = input("เลือกหมายเลข > ").strip()
        if not raw:
            print("ยกเลิก: ไม่มีการเลือก")
            return None
        choice = int(raw)
    except (ValueError, EOFError, KeyboardInterrupt):
        print("Invalid input — บอกเป็นตัวเลข 1..6 เท่านั้น")
        return None

    if choice < 1 or choice > len(MENU):
        print("ตัวเลือกไม่ถูกต้อง")
        return None

    label, key = MENU[choice - 1]
    if key == "cancel":
        print("ยกเลิกโดยผู้ใช้")
        return None

    if key == "custom":
        # custom input
        while True:
            try:
                raw_lvl = input("ระบุ Level (ตัวเลขเต็ม >=0) > ").strip()
                if raw_lvl == "":
                    print("ยกเลิก custom")
                    return None
                lvl = int(raw_lvl)
                if lvl < 0:
                    print("กรุณาใส่ตัวเลข >= 0")
                    continue
                return lvl
            except ValueError:
                print("กรุณาใส่ตัวเลขเต็ม")
            except (KeyboardInterrupt, EOFError):
                print("\nยกเลิก custom")
                return None

    # normal mapping (do not display number to user)
    return _SKILL_MAPPING.get(key)


def launch_bot_with_skill(skill_level: int) -> int:
    """
    Launch bot.py as subprocess with STOCKFISH_SKILL environment variable set.
    Returns subprocess exit code.
    """
    env = os.environ.copy()
    env["STOCKFISH_SKILL"] = str(skill_level)
    # keep other envs (e.g. TOKEN stored in config.py)
    python_exe = sys.executable or "python"
    cmd = [python_exe, "bot.py"]
    print(f"\nStarting bot with chosen profile... (skill hidden)")
    print("If you need to change token or other settings, edit config.py before running.")
    try:
        # run until bot.py exits; pass through stdout/stderr
        proc = subprocess.run(cmd, env=env)
        return proc.returncode
    except KeyboardInterrupt:
        print("Interrupted by user")
        return 130
    except FileNotFoundError:
        print("ไม่พบไฟล์ bot.py ในโฟลเดอร์นี้")
        return 2
    except Exception as e:
        print("Error when launching bot:", e)
        return 3


def main():
    clear_screen()
    choice = prompt_choice()
    if choice is None:
        print("ไม่มีการเริ่มบอท")
        return
    # show minimal feedback but do NOT print numeric mapping for built-in choices
    print("กำลังเริ่มบอท (จะไม่แสดง level ที่แท้จริงสำหรับตัวเลือกมาตรฐาน)...")
    # but for debugging you could print skill number if you want:
    # print("DEBUG: skill level =", choice)

    rc = launch_bot_with_skill(choice)
    print(f"Bot process returned code: {rc}")


if __name__ == "__main__":
    main()

