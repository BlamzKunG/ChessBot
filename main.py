# server.py — guaranteed top-5 fallback (per-move scoring)
import asyncio
import websockets
import json
import chess
import chess.engine
import os
import time

WEBSOCKET_HOST = "localhost"
WEBSOCKET_PORT = 8765

STOCKFISH_PATH = r"C:\Users\Blam\Documents\cb\stockfish.exe"
MULTIPV = 3
DEPTH = 8  # ปรับ tradeoff speed/quality

board = chess.Board()

if not os.path.isfile(STOCKFISH_PATH):
    raise FileNotFoundError("Stockfish not found. ตั้งค่า STOCKFISH_PATH ให้ถูกต้อง.")

engine = chess.engine.SimpleEngine.popen_uci(STOCKFISH_PATH)

def try_set_multipv(n):
    try:
        engine.configure({"MultiPV": n})
        return True
    except Exception:
        return False

def score_to_numeric(score_obj, perspective_color):
    """
    Convert a chess.engine.Score to a numeric value from perspective_color viewpoint.
    Higher = better for perspective_color.
    Returns (numeric_value, cp_or_none, mate_or_none)
    """
    if score_obj is None:
        return None, None, None
    try:
        s = score_obj.pov(perspective_color)  # Score from perspective of perspective_color
    except Exception:
        # fallback: try white(), then invert if perspective is black
        try:
            s = score_obj.white()
            if perspective_color == chess.BLACK:
                # invert
                if s.is_mate():
                    return (-1 if s.mate() > 0 else 1) * 100000, None, s.mate()
                else:
                    return -s.score(), -s.score(), None
        except Exception:
            return None, None, None

    if s.is_mate():
        mate = s.mate()  # positive means mate for perspective_color
        # larger positive is better (mate in N), larger negative is worse
        numeric = 100000 if mate > 0 else -100000
        # we keep mate signed as returned
        return numeric, None, mate
    else:
        cp = s.score()
        return cp, cp, None

async def handler(ws):
    global board, engine
    async for msg in ws:
        try:
            moves = json.loads(msg)
            if not isinstance(moves, list):
                await ws.send(json.dumps({"error": "Expected list of moves"}))
                continue

            # sync board
            current_ply = len(board.move_stack)
            if len(moves) <= current_ply:
                board.reset()
                current_ply = 0

            failed = False
            for i in range(current_ply, len(moves)):
                san = moves[i]
                try:
                    mv = board.parse_san(san)
                    board.push(mv)
                except Exception as e:
                    print("Cannot parse SAN:", san, "err:", e)
                    board.reset()
                    failed = True
                    break

            if failed:
                await ws.send(json.dumps({"status": "reset"}))
                continue

            # Try to set multipv
            try_set_multipv(MULTIPV)

            # First attempt: one analyse call (best-effort MultiPV)
            pvs = []
            try:
                info = engine.analyse(board, chess.engine.Limit(depth=DEPTH))
                entries = info if isinstance(info, list) else [info]
                for ent in entries[:MULTIPV]:
                    pv = ent.get("pv")
                    if not pv or len(pv) == 0:
                        continue
                    first_move = pv[0]
                    uci_move = first_move.uci() if isinstance(first_move, chess.Move) else str(first_move)
                    score_obj = ent.get("score")
                    numeric, cp, mate = score_to_numeric(score_obj, board.turn)
                    pvs.append({"move": uci_move, "score_cp": cp, "mate": mate, "numeric": numeric})
            except Exception as e:
                print("analyse() exception:", e)
                pvs = []

            # If we didn't get enough PVs, fallback to per-legal-move scoring (guaranteed)
            if len(pvs) < MULTIPV:
                # Evaluate every legal move individually using root_moves to get its score,
                # then sort and pick top MULTIPV — accurate but heavier.
                legal = list(board.legal_moves)
                scored = []
                for mv in legal:
                    try:
                        # engine.analyse with root_moves gives score for that move as the root move
                        info = engine.analyse(board, chess.engine.Limit(depth=DEPTH), root_moves=[mv])
                        # info may be dict
                        ent = info if isinstance(info, dict) else (info[0] if isinstance(info, list) and len(info) > 0 else None)
                        if not ent:
                            continue
                        score_obj = ent.get("score")
                        numeric, cp, mate = score_to_numeric(score_obj, board.turn)
                        scored.append({
                            "move": mv.uci(),
                            "score_cp": cp,
                            "mate": mate,
                            "numeric": numeric
                        })
                    except Exception as e:
                        # ignore individual move failures but continue
                        print("per-move analyse failed for", mv, e)
                        continue

                # filter out None numeric (failed ones), sort descending by numeric (best first)
                scored = [s for s in scored if s.get("numeric") is not None]
                scored.sort(key=lambda x: x["numeric"], reverse=True)
                # if we already had some pvs from first attempt, merge them with per-move results, dedupe by move
                seen = set([entry["move"] for entry in pvs])
                merged = pvs.copy()
                for s in scored:
                    if s["move"] in seen:
                        continue
                    merged.append({"move": s["move"], "score_cp": s["score_cp"], "mate": s["mate"], "numeric": s["numeric"]})
                    seen.add(s["move"])
                    if len(merged) >= MULTIPV:
                        break
                pvs = merged[:MULTIPV]

            # Final safety: if still empty, fallback to engine.play once
            if not pvs:
                try:
                    mv = engine.play(board, chess.engine.Limit(depth=DEPTH)).move
                    pvs = [{"move": mv.uci(), "score_cp": None, "mate": None, "numeric": None}]
                except Exception as e:
                    print("play() fallback error:", e)
                    pvs = []

            # prune numeric before sending
            out = []
            for entry in pvs[:MULTIPV]:
                out.append({
                    "move": entry.get("move"),
                    "score_cp": entry.get("score_cp"),
                    "mate": entry.get("mate")
                })

            payload = {"pvs": out, "fen": board.fen()}
            await ws.send(json.dumps(payload))
            print("Sent analysis:", payload)

        except json.JSONDecodeError:
            await ws.send(json.dumps({"error": "Invalid JSON"}))

async def main():
    async with websockets.serve(handler, WEBSOCKET_HOST, WEBSOCKET_PORT):
        print(f"WebSocket server running on ws://{WEBSOCKET_HOST}:{WEBSOCKET_PORT}")
        await asyncio.Future()

try:
    asyncio.run(main())
finally:
    try:
        engine.quit()
    except Exception:
        pass
