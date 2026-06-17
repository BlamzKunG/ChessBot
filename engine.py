from __future__ import annotations

import os
import time
from typing import Optional, Any

import chess
import chess.engine
from chess.engine import EngineTerminatedError, EngineError


def _read_skill_env() -> Optional[int]:
    for key in ("STOCKFISH_SKILL", "BOT_SKILL_LEVEL", "START_BOT_SKILL"):
        v = os.environ.get(key)
        if v is not None:
            try:
                return int(v)
            except Exception:
                print(f"[engine] env {key} exists but is not an integer: {v!r}; ignoring.")
    return None


def _clamp_skill_for_stockfish(skill: int) -> int:
    """Clamp skill to Stockfish-supported range (0..20)."""
    try:
        s = int(skill)
    except Exception:
        return 3
    if s < 0:
        return 0
    if s > 20:
        return 20
    return s


class Engine:
    def __init__(
        self,
        path: str = "stockfish",
        skill_level: Optional[int] = None,
        threads: int = 2,
        hash_mb: int = 64,
        default_time: Optional[float] = None,
        default_depth: Optional[int] = 15,
    ) -> None:
        # determine effective skill: priority -> arg > env > default(3)
        env_skill = _read_skill_env()
        if skill_level is None and env_skill is None:
            effective = 20 # Default to max skill for better performance
        else:
            effective = skill_level if skill_level is not None else env_skill  # type: ignore

        self.path = path
        self.custom_skill = None
        try:
            effective = int(effective)
        except Exception:
            effective = 20

        if effective > 20:
            self.custom_skill = effective
        self.skill_level = _clamp_skill_for_stockfish(effective)
        self.threads = max(1, int(threads))
        self.hash_mb = max(1, int(hash_mb))
        self.default_time = default_time
        self.default_depth = default_depth or 15

        self._engine: Optional[chess.engine.SimpleEngine] = None
        self._last_eval: Optional[chess.engine.Score] = None
        self._start_engine()

    def _start_engine(self) -> None:
        if self._engine:
            return
        try:
            # Try to find stockfish in path if not specified correctly
            import shutil
            actual_path = shutil.which(self.path) or self.path
            self._engine = chess.engine.SimpleEngine.popen_uci(actual_path)
        except Exception as e:
            raise RuntimeError(f"Cannot start Stockfish at '{self.path}': {e}") from e

        try:
            self._engine.configure({
                "Skill Level": int(self.skill_level),
                "Threads": int(self.threads),
                "Hash": int(self.hash_mb),
                "MultiPV": 3 # For complexity analysis
            })
        except Exception as e:
            print(f"[engine] Configuration error: {e}")

    def calculate_time(self, board: chess.Board, wtime: float, btime: float, winc: float = 0, binc: float = 0) -> float:
        """
        Calculate thinking time based on remaining clock and game complexity.
        Times are in milliseconds.
        """
        try:
            from config import MOVE_OVERHEAD, MIN_TIME, MAX_TIME
        except ImportError:
            MOVE_OVERHEAD, MIN_TIME, MAX_TIME = 500, 0.1, 10.0

        my_time = wtime if board.turn == chess.WHITE else btime
        my_inc = winc if board.turn == chess.WHITE else binc
        
        if my_time is None: my_time = 60000 # Fallback
        
        # 0. Panic Mode / Ultra Speed (User request)
        # If we have less than 1.5s (+ overhead), move extremely fast to avoid flagging.
        if my_time < (1500 + MOVE_OVERHEAD):
            # Still try to give it a tiny bit of time if possible, but prioritize speed.
            panic_time = max(0.05, (my_time - MOVE_OVERHEAD) / 1000.0 / 2)
            print(f"[engine] Panic Mode! Time: {my_time}ms. Moving at {panic_time:.3f}s")
            return panic_time

        # Base time: roughly 1/30th to 1/10th of remaining time
        if my_time > 60000: # More than 1 min
            base_time = my_time / 30 + my_inc * 0.8
        elif my_time > 20000: # 20s - 1min
            base_time = my_time / 20 + my_inc * 0.8
        else: # 2s - 20s
            base_time = my_time / 10 + my_inc * 0.9

        # Adjust for Complexity
        multiplier = 1.0
        
        # 1. Material Balance (Endgame check)
        material_count = sum(len(board.pieces(p, c)) for p in chess.PIECE_TYPES for c in chess.COLORS)
        if material_count < 12:
            multiplier *= 1.3 # Endgames need more precision
            
        # 2. Score Change & Multi-PV Analysis
        if self._engine:
            try:
                # Quick 100ms analysis to gauge the situation
                info = self._engine.analyse(board, chess.engine.Limit(time=0.1), multipv=2)
                if info:
                    current_eval = info[0]["score"].relative
                    # Convert mate to a large score
                    score = current_eval.score() if not current_eval.is_mate() else (-10000 if current_eval.mate() < 0 else 10000)
                    
                    # 3. Losing position logic (User request)
                    # If losing, think much longer to find a way out.
                    if score < -500: # Down by a rook or more
                        print(f"[engine] Critical disadvantage ({score}). Thinking 4x longer.")
                        multiplier *= 4.0
                    elif score < -150: # Down by 1.5 pawns
                        print(f"[engine] Significant disadvantage ({score}). Thinking 2.5x longer.")
                        multiplier *= 2.5
                    
                    # 4. Critical Score Change
                    if self._last_eval is not None:
                        try:
                            last_score = self._last_eval.score() if not self._last_eval.is_mate() else (-10000 if self._last_eval.mate() < 0 else 10000)
                            diff = score - last_score
                            if diff < -100: # Position getting worse
                                multiplier *= 1.5
                        except: pass
                    
                    self._last_eval = current_eval
                    
                    # 5. Competition between moves
                    if len(info) >= 2:
                        try:
                            s1 = info[0]["score"].relative.score()
                            s2 = info[1]["score"].relative.score()
                            if s1 is not None and s2 is not None and abs(s1 - s2) < 25:
                                multiplier *= 1.3 # Hard choice between two good moves
                        except: pass
            except Exception as e:
                pass # Analysis failed, use base time

        final_time = (base_time * multiplier) / 1000.0
        
        # Safety: Never spend more than 20% of remaining time (minus overhead)
        max_allowed = max(MIN_TIME, (my_time - MOVE_OVERHEAD) / 1000.0 * 0.25)
        
        return max(MIN_TIME, min(final_time, MAX_TIME, max_allowed))

    def _choose_move_from_board(
        self,
        board: chess.Board,
        *,
        time_limit: Optional[float] = None,
        depth: Optional[int] = None,
        wtime: Optional[float] = None,
        btime: Optional[float] = None,
        winc: Optional[float] = None,
        binc: Optional[float] = None,
    ) -> Optional[str]:
        if board.is_game_over():
            return None

        # Start engine FIRST so calculate_time can use it
        if self._engine is None:
            self._start_engine()

        if wtime is not None and btime is not None:
            # Dynamic time management
            calc_time = self.calculate_time(board, wtime, btime, winc or 0, binc or 0)
            limit = chess.engine.Limit(time=calc_time)
        elif time_limit is not None:
            limit = chess.engine.Limit(time=time_limit)
        else:
            limit = chess.engine.Limit(depth=depth or self.default_depth)

        try:
            result = self._engine.play(board, limit)
            if result is None or result.move is None:
                return None
            return result.move.uci()
        except Exception as e:
            print(f"[engine] play error: {e}")
            self._engine = None # Force restart next time
            return None

    # -------------------------
    # payload -> board helpers
    # -------------------------
    @staticmethod
    def _extract_moves_from_payload(payload: Any) -> str:
        if payload is None:
            return ""
        if isinstance(payload, str):
            if "/" in payload and " " in payload:
                return ""
            return payload.strip()
        if isinstance(payload, dict):
            if "moves" in payload and isinstance(payload["moves"], str):
                return payload["moves"].strip()
            if "state" in payload and isinstance(payload["state"], dict):
                return payload["state"].get("moves", "").strip()
            if payload.get("type") == "gameFull" and isinstance(payload.get("state"), dict):
                return payload["state"].get("moves", "").strip()
        return ""

    def _board_from_game_state(self, game_state: Any) -> chess.Board:
        if isinstance(game_state, str) and "/" in game_state and " " in game_state:
            return chess.Board(fen=game_state)
        moves_str = self._extract_moves_from_payload(game_state)
        board = chess.Board()
        if moves_str:
            for mv in moves_str.split():
                try:
                    board.push_uci(mv)
                except Exception:
                    continue
        return board

    # -------------------------
    # runtime config
    # -------------------------
    def set_skill_level(self, level: int) -> None:
        """Set skill at runtime. This will clamp to 0..20 for engine configure."""
        try:
            lvl = int(level)
        except Exception:
            print(f"[engine] set_skill_level: invalid value {level!r}")
            return
        if lvl > 20:
            self.custom_skill = lvl
            print(f"[engine] requested skill {lvl} > 20; clamping to 20 for Stockfish.")
        else:
            self.custom_skill = None
        self.skill_level = _clamp_skill_for_stockfish(lvl)
        if self._engine:
            try:
                self._engine.configure({"Skill Level": int(self.skill_level)})
                print(f"[engine] Skill Level updated to {self.skill_level}")
            except Exception:
                print("[engine] Skill Level option not supported by this engine build; ignored.")

    def apply_env_skill(self) -> None:
        """Read environment variable again and apply as new skill (if present)."""
        env = _read_skill_env()
        if env is None:
            print("[engine] apply_env_skill: no env skill found")
            return
        self.set_skill_level(env)

    def set_threads(self, threads: int) -> None:
        self.threads = max(1, int(threads))
        if self._engine:
            try:
                self._engine.configure({"Threads": self.threads})
                print(f"[engine] Threads updated to {self.threads}")
            except Exception:
                pass

    def set_hash(self, mb: int) -> None:
        self.hash_mb = max(1, int(mb))
        if self._engine:
            try:
                self._engine.configure({"Hash": self.hash_mb})
                print(f"[engine] Hash updated to {self.hash_mb}MB")
            except Exception:
                pass

    # -------------------------
    # cleanup
    # -------------------------
    def close(self) -> None:
        if self._engine:
            try:
                self._engine.quit()
            except Exception:
                pass
            self._engine = None


# -------------------------
# quick manual smoke test (do not run in bot loop)
# -------------------------
if __name__ == "__main__":
    # You can set env first, e.g.:
    #   set STOCKFISH_SKILL=10  (Windows)
    #   export STOCKFISH_SKILL=10  (Linux/macOS)
    # Or pass skill_level directly below.
    e = Engine(path="stockfish.exe", skill_level=None, threads=2, hash_mb=32, default_time=None, default_depth=6)
    print("[test] Effective skill:", e.skill_level, "custom_skill:", e.custom_skill)
    t0 = time.time()
    mv = e.get_best_move(chess.STARTING_FEN, time_limit=0.05)
    print("time-based move:", mv, "took:", time.time() - t0)
    t0 = time.time()
    mv2 = e.get_best_move(chess.STARTING_FEN, depth=6)
    print("depth-based move:", mv2, "took:", time.time() - t0)
    e.close()

