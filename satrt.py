from __future__ import annotations
import os
import sys
import subprocess
import shutil
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

def clear_screen() -> None:
    if os.name == "nt":
        os.system("cls")
    else:
        os.system("clear")

def check_stockfish() -> Optional[str]:
    """Check if stockfish is available in PATH or current folder."""
    # Check current folder for common names
    for name in ["stockfish", "stockfish.exe", "stockfish_15", "stockfish-windows-x86-64-avx2.exe"]:
        if os.path.exists(name):
            return os.path.abspath(name)
    
    # Check in PATH
    path = shutil.which("stockfish")
    if path:
        return path
        
    return None

def launch_bot() -> int:
    """
    Launch bot.py with Dynamic Mode enabled by default.
    """
    env = os.environ.copy()
    
    # บังคับใช้ Skill สูงสุดและเปิด Dynamic Mode
    env["STOCKFISH_SKILL"] = "20"
    env["DYNAMIC_MODE"] = "1"
    
    # ตรวจสอบ Stockfish path
    sf_path = check_stockfish()
    if sf_path:
        env["STOCKFISH_PATH"] = sf_path
        print(f"[*] Found Stockfish at: {sf_path}")
    else:
        print("[!] Warning: Stockfish not found in PATH or folder. Please ensure it is installed.")

    python_exe = sys.executable or "python"
    cmd = [python_exe, "bot.py"]
    
    print(f"\n[+] Starting Bot in DYNAMIC MODE (The smartest version)...")
    print("[+] Adjusting thinking time based on position complexity...")
    print("[+] Monitoring clock and network latency...")
    print("\nPress Ctrl+C to stop the bot.\n")
    
    try:
        proc = subprocess.run(cmd, env=env)
        return proc.returncode
    except KeyboardInterrupt:
        print("\n[!] Bot stopped by user.")
        return 130
    except Exception as e:
        print(f"\n[!] Error: {e}")
        return 1

def main():
    clear_screen()
    print(ASCII_TITLE)
    print(" " * 20 + "--- CHESSBOT DYNAMIC EDITION ---")
    print("\n" + "="*60)
    
    # ตรวจสอบ TOKEN เบื้องต้น
    from config import TOKEN
    if not TOKEN or TOKEN == "token":
        print("[!] Error: ไม่พบ Lichess Token ใน config.py")
        print("[!] กรุณาใส่ Token ของคุณในไฟล์ config.py ก่อนเริ่มใช้งาน")
        return

    launch_bot()

if __name__ == "__main__":
    main()
