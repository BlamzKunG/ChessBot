# bot.py (แก้ให้พร้อมใช้งานกับ engine.choose_move)
import threading
import time
import traceback
import berserk
import berserk.exceptions
from config import TOKEN, POLL_INTERVAL
from engine import Engine
import chess  # สำหรับ validate UCI

# สร้าง session และ client
session = berserk.TokenSession(TOKEN)
client = berserk.Client(session=session)

# สร้าง instance ของ engine ที่จะใช้ตลอดโปรแกรม
# ปรับ mode เป็น "random" / "minimax" / "stockfish" ตามต้องการ
engine_inst = Engine(mode="minimax", random_seed=0, stockfish_path=None)


def _parse_moves_from_state(state):
    if not state:
        return ""
    if isinstance(state, dict):
        if "moves" in state:
            return state.get("moves", "") or ""
        if "state" in state and isinstance(state["state"], dict):
            return state["state"].get("moves", "") or ""
        if state.get("type") == "gameFull" and isinstance(state.get("state"), dict):
            return state["state"].get("moves", "") or ""
        return ""
    if isinstance(state, str):
        return state
    return ""


def handle_game(game_id: str, my_color: str):
    print(f"[handler] start game handler {game_id} (color={my_color})")
    last_processed_moves_count = -1

    # Try using streaming game state (preferred)
    try:
        stream = client.bots.stream_game_state(game_id)
    except Exception:
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
                        # เรียก engine ให้คืน UCI string
                        try:
                            move = engine_inst.choose_move(state, depth=2, time_limit=0.05)
                        except Exception as e:
                            print(f"[{game_id}] engine exception: {e}")
                            move = None

                        # Validate move (UCI string) ก่อนส่ง
                        if move and isinstance(move, str):
                            try:
                                chess.Move.from_uci(move)
                            except Exception:
                                print(f"[{game_id}] engine returned invalid UCI: {move!r}")
                                move = None

                        if move:
                            try:
                                client.bots.make_move(game_id, move)
                                print(f"[handler:{game_id}] ส่ง move {move} (moves_count={moves_count})")
                                last_processed_moves_count = moves_count
                            except berserk.exceptions.ResponseError as err:
                                print(f"[handler:{game_id}] ไม่สามารถส่ง move: {err}")
                        else:
                            print(f"[handler:{game_id}] engine คืน None (no move).")
                except Exception:
                    print(f"[handler:{game_id}] error processing state:\n{traceback.format_exc()}")
                    time.sleep(POLL_INTERVAL)
        except Exception:
            print(f"[handler:{game_id}] stream ตัด, fallback เป็น polling")

    # Fallback: polling using client.games.export
    try:
        while True:
            try:
                game_state = client.games.export(game_id)
            except berserk.exceptions.ResponseError as e:
                print(f"[handler:{game_id}] ไม่สามารถดึงสถานะเกม (export): {e}")
                break

            status = game_state.get("status")
            if status and status != "started":
                print(f"[handler:{game_id}] เกมจบ (status={status})")
                break

            moves_str = game_state.get("moves", "") or ""
            moves_list = moves_str.split() if moves_str else []
            moves_count = len(moves_list)

            to_move_color = "white" if (moves_count % 2 == 0) else "black"

            if to_move_color == my_color and last_processed_moves_count != moves_count:
                # ใช้ game_state เป็น input ใน polling
                try:
                    move = engine_inst.choose_move(game_state, depth=2, time_limit=0.05)
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
                    try:
                        client.bots.make_move(game_id, move)
                        print(f"[handler:{game_id}] (poll) ส่ง move {move} (moves_count={moves_count})")
                        last_processed_moves_count = moves_count
                    except berserk.exceptions.ResponseError as err:
                        print(f"[handler:{game_id}] (poll) ไม่สามารถส่ง move: {err}")
                else:
                    print(f"[handler:{game_id}] (poll) engine คืน None")
            time.sleep(POLL_INTERVAL)
    except Exception:
        print(f"[handler:{game_id}] handler exception:\n{traceback.format_exc()}")

    print(f"[handler] end game handler {game_id}")


def main():
    print("Bot เริ่มทำงาน... รอ challenge...")
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
            print(f"error in main event loop:\n{traceback.format_exc()}")


if __name__ == "__main__":
    main()
