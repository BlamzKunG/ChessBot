import threading
import time
import traceback
import sys
import os
import shutil

import berserk
import berserk.exceptions
import requests
import chess

from config import TOKEN, POLL_INTERVAL, STOCKFISH_PATH
from engine import Engine  

client = None

# ------- Stockfish Auto-Discovery -------
def check_stockfish(configured_path):
    """Check if stockfish is available in configured path, PATH, or current folder."""
    if configured_path and os.path.exists(configured_path):
        return configured_path
        
    for name in ["stockfish", "stockfish.exe", "stockfish_15", "stockfish-windows-x86-64-avx2.exe"]:
        if os.path.exists(name):
            return os.path.abspath(name)
    
    path = shutil.which("stockfish")
    if path:
        return path
    return configured_path # fallback

# ------- Instantiate engine -------
def _make_engine_instance():
    sf_path = check_stockfish(STOCKFISH_PATH)
    print(f"[*] Using Stockfish at: {sf_path}")
    try:
        # ใช้ Engine พร้อม Dynamic Time Management
        return Engine(path=sf_path, skill_level=20)
    except Exception as e:
        print(f"[!] Warning: Engine start failed: {e}. Attempting simple init.")
        try:
            return Engine()
        except:
            raise RuntimeError(f"ไม่สามารถสร้าง Engine instance ได้: {e}")

engine_inst = _make_engine_instance()

# ------- client/session helper -------
def create_client():
    """(Re)create berserk client/session and assign to global client."""
    global client
    if not TOKEN or TOKEN == "token":
        print("[!] Error: ไม่พบ Lichess Token ใน config.py")
        sys.exit(1)
    session = berserk.TokenSession(TOKEN)
    client = berserk.Client(session=session)
    return client

# create initial client
create_client()

# ------- Engine call wrapper (Simplified & Robust) -------
def call_engine_for_move(game_state):
    # Extract clock info if available
    wtime, btime, winc, binc = None, None, None, None
    
    if isinstance(game_state, dict):
        state = game_state.get("state", game_state)
        wtime = state.get("wtime")
        btime = state.get("btime")
        winc = state.get("winc")
        binc = state.get("binc")

    board = _board_from_game_state(game_state)
    
    try:
        # พยายามใช้การคำนวณแบบ Dynamic ก่อน
        move_uci = engine_inst._choose_move_from_board(
            board, 
            wtime=wtime, 
            btime=btime, 
            winc=winc, 
            binc=binc
        )
        if move_uci:
            return move_uci
    except Exception as e:
        print(f"[engine] dynamic choice failed: {e}")

    # Fallback: ใช้ simple move แบบเวอร์ชันเก่าที่เสถียร
    try:
        return engine_inst._choose_move_from_board(board, depth=15)
    except Exception as e:
        print(f"[engine] fallback failed: {e}")
        return None

# ------- helper: parse/board -------
def _parse_moves_from_state(state):
    if not state: return ""
    if isinstance(state, dict):
        if "moves" in state: return state.get("moves", "") or ""
        if "state" in state and isinstance(state["state"], dict):
            return state["state"].get("moves", "") or ""
        if state.get("type") == "gameFull" and isinstance(state.get("state"), dict):
            return state["state"].get("moves", "") or ""
        if state.get("type") == "gameState": # Lichess stream state
            return state.get("moves", "") or ""
    return str(state) if isinstance(state, str) else ""


def _board_from_game_state(game_state):
    if isinstance(game_state, str):
        if "/" in game_state and " " in game_state:
            try:
                return chess.Board(fen=game_state)
            except Exception:
                pass
        moves_str = game_state.strip()
    elif isinstance(game_state, dict):
        moves_str = ""
        if "moves" in game_state:
            moves_str = game_state.get("moves", "") or ""
        elif "state" in game_state and isinstance(game_state["state"], dict):
            moves_str = game_state["state"].get("moves", "") or ""
        elif game_state.get("type") == "gameFull" and isinstance(game_state.get("state"), dict):
            moves_str = game_state["state"].get("moves", "") or ""
        else:
            moves_str = ""
    else:
        moves_str = ""

    board = chess.Board()
    if moves_str:
        for m in moves_str.split():
            try:
                board.push_uci(m)
            except Exception:
                continue
    return board


# ------- safe move sender -------
def make_move_safe(game_id: str, move: str, max_retries: int = 3, retry_delay: float = 1.0) -> bool:
    """
    พยายามส่ง move ซ้ำ ๆ ถ้ามีปัญหา network (ไม่ใช่ข้อผิดพลาดแบบ 'Not your turn').
    คืน True ถ้าส่งสำเร็จ, False ถ้าไม่สำเร็จ
    """
    for attempt in range(1, max_retries + 1):
        try:
            client.bots.make_move(game_id, move)
            return True
        except berserk.exceptions.ResponseError as err:
            # ถ้าเป็นข้อผิดพลาดว่า "Not your turn" หรือ "Invalid UCI" -> ไม่ retry
            msg = str(err)
            if "Not your turn" in msg or "Invalid UCI" in msg or "is not your game" in msg:
                print(f"[{game_id}] make_move failed (non-retryable): {err}")
                return False
            # network-related or server errors -> retry
            print(f"[{game_id}] make_move attempt {attempt} failed: {err}. retrying in {retry_delay}s...")
            time.sleep(retry_delay)
        except requests.exceptions.RequestException as e:
            print(f"[{game_id}] network error when making move: {e}. retrying in {retry_delay}s...")
            time.sleep(retry_delay)
        except Exception as e:
            print(f"[{game_id}] unexpected error in make_move: {e}")
            time.sleep(retry_delay)
    return False


# ------- game handler -------
def handle_game(game_id: str, my_color: str):
    print(f"[handler] start game handler {game_id} (color={my_color})")
    last_processed_moves_count = -1

    # Try using streaming game state (preferred)
    try:
        stream = client.bots.stream_game_state(game_id)
    except Exception as e:
        print(f"[handler:{game_id}] cannot open game stream: {e}")
        stream = None

    if stream:
        try:
            for state in stream:
                try:
                    moves_str = _parse_moves_from_state(state)
                    moves_list = moves_str.split() if moves_str else []
                    moves_count = len(moves_list)

                    status = None
                    if isinstance(state, dict):
                        if "state" in state and isinstance(state["state"], dict):
                            status = state["state"].get("status")
                        else:
                            status = state.get("status")

                    if status and status != "started":
                        print(f"[handler:{game_id}] เกมจบ (status={status})")
                        break

                    to_move_color = "white" if (moves_count % 2 == 0) else "black"

                    if to_move_color == my_color and last_processed_moves_count != moves_count:
                        try:
                            move = call_engine_for_move(state)
                        except Exception as e:
                            print(f"[{game_id}] engine exception: {e}")
                            move = None

                        # Validate move
                        if move and isinstance(move, str):
                            try:
                                chess.Move.from_uci(move)
                            except Exception:
                                print(f"[{game_id}] engine returned invalid UCI: {move!r}")
                                move = None

                        if move:
                            ok = make_move_safe(game_id, move)
                            if ok:
                                print(f"[handler:{game_id}] ส่ง move {move} (moves_count={moves_count})")
                                last_processed_moves_count = moves_count
                            else:
                                print(f"[handler:{game_id}] failed to send move {move}")
                        else:
                            print(f"[handler:{game_id}] engine คืน None (no move).")
                except Exception:
                    print(f"[handler:{game_id}] error processing state:\n{traceback.format_exc()}")
                    time.sleep(POLL_INTERVAL)
        except Exception as e:
            print(f"[handler:{game_id}] stream exception (will fallback to polling): {e}")
            # fall-through to polling
    # Fallback: polling using client.games.export
    try:
        while True:
            try:
                game_state = client.games.export(game_id)
            except berserk.exceptions.ResponseError as e:
                # network/server issue - retry after a pause instead of breaking handler
                print(f"[handler:{game_id}] export error (network/server): {e}. retrying in {POLL_INTERVAL}s")
                time.sleep(max(0.5, POLL_INTERVAL))
                continue
            except requests.exceptions.RequestException as e:
                print(f"[handler:{game_id}] network error on export: {e}. retrying in {POLL_INTERVAL}s")
                time.sleep(max(0.5, POLL_INTERVAL))
                continue
            except Exception as e:
                print(f"[handler:{game_id}] unexpected export error: {e}")
                time.sleep(max(0.5, POLL_INTERVAL))
                continue

            status = game_state.get("status")
            if status and status != "started":
                print(f"[handler:{game_id}] เกมจบ (status={status})")
                break

            moves_str = game_state.get("moves", "") or ""
            moves_list = moves_str.split() if moves_str else []
            moves_count = len(moves_list)

            to_move_color = "white" if (moves_count % 2 == 0) else "black"

            if to_move_color == my_color and last_processed_moves_count != moves_count:
                try:
                    move = call_engine_for_move(game_state)
                except Exception as e:
                    print(f"[{game_id}] engine exception (poll): {e}")
                    move = None

                if move and isinstance(move, str):
                    try:
                        chess.Move.from_uci(move)
                    except Exception:
                        print(f"[{game_id}] engine returned invalid UCI (poll): {move!r}")
                        move = None

                if move:
                    ok = make_move_safe(game_id, move)
                    if ok:
                        print(f"[handler:{game_id}] (poll) ส่ง move {move} (moves_count={moves_count})")
                        last_processed_moves_count = moves_count
                    else:
                        print(f"[handler:{game_id}] (poll) failed to send move {move}")
                else:
                    print(f"[handler:{game_id}] (poll) engine คืน None")
            time.sleep(POLL_INTERVAL)
    except Exception:
        print(f"[handler:{game_id}] handler exception:\n{traceback.format_exc()}")

    print(f"[handler] end game handler {game_id}")


# ------- main event loop with reconnect/backoff -------
def main():
    print("Bot เริ่มทำงาน... รอ challenge...")
    backoff = 1.0  # initial backoff (seconds)
    while True:
        try:
            # ensure client exists (create_client sets global client)
            if client is None:
                create_client()

            # iterate events; if stream breaks it will throw and be caught below
            for event in client.bots.stream_incoming_events():
                try:
                    etype = event.get("type")
                    if etype == "challenge":
                        challenge_id = event["challenge"]["id"]
                        print(f"มี challenge ใหม่: {challenge_id}, ตอบรับ...")
                        try:
                            client.bots.accept_challenge(challenge_id)
                        except berserk.exceptions.ResponseError as e:
                            print(f"ไม่สามารถตอบรับ challenge: {e}")
                        continue

                    if etype == "gameStart":
                        game_id = event["game"]["id"]
                        my_color = event["game"].get("color")  # "white" or "black"
                        t = threading.Thread(target=handle_game, args=(game_id, my_color), daemon=True)
                        t.start()
                except Exception:
                    print(f"error in main event loop event processing:\n{traceback.format_exc()}")

            # if loop exits normally (rare), reset backoff and loop again
            backoff = 1.0

        except (requests.exceptions.RequestException,
                berserk.exceptions.ResponseError,
                Exception) as e:
            # Generic catch: print, sleep with exponential backoff, recreate client, and retry
            print(f"[main] stream error / disconnected: {e}")
            print(f"[main] reconnecting in {backoff:.1f}s...")
            try:
                time.sleep(backoff)
            except KeyboardInterrupt:
                print("Stopping on keyboard interrupt.")
                try:
                    if hasattr(engine_inst, "close"):
                        engine_inst.close()
                except Exception:
                    pass
                sys.exit(0)
            # exponential backoff up to 60s
            backoff = min(backoff * 2.0, 60.0)
            # recreate client/session to recover from stale connection
            try:
                create_client()
            except Exception as ce:
                print(f"[main] failed to recreate client: {ce}")
                # continue loop -> will attempt again
                continue


if __name__ == "__main__":
    main()

