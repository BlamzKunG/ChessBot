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
        default_depth: Optional[int] = None,
    ) -> None:
        # determine effective skill: priority -> arg > env > default(3)
        env_skill = _read_skill_env()
        if skill_level is None and env_skill is None:
            effective = 3
        else:
            effective = skill_level if skill_level is not None else env_skill  # type: ignore

        self.path = path
        self.custom_skill = None  # if user supplied >20 we keep original here for reference
        try:
            effective = int(effective)
        except Exception:
            effective = 3

        # keep user-specified as-is in custom_skill if out-of-range
        if effective > 20:
            self.custom_skill = effective
            print(f"[engine] Note: requested skill {effective} > 20; will clamp to 20 for Stockfish.")
        self.skill_level = _clamp_skill_for_stockfish(effective)
        self.threads = max(1, int(threads))
        self.hash_mb = max(1, int(hash_mb))
        self.default_time = default_time
        self.default_depth = default_depth or 8

        self._engine: Optional[chess.engine.SimpleEngine] = None
        self._start_engine()

    def _start_engine(self) -> None:
        """Start stockfish process and configure options. If fails, raise exception."""
        if self._engine:
            return
        try:
            self._engine = chess.engine.SimpleEngine.popen_uci(self.path)
        except Exception as e:
            raise RuntimeError(f"Cannot start Stockfish at '{self.path}': {e}") from e

        # Configure options, guarded because not all builds support all options:
        try:
            # Skill Level might not exist; ignore errors
            self._engine.configure({"Skill Level": int(self.skill_level)})
        except Exception:
            pass
        try:
            self._engine.configure({"Threads": int(self.threads)})
        except Exception:
            pass
        try:
            self._engine.configure({"Hash": int(self.hash_mb)})
        except Exception:
            pass

        print(f"[engine] Started Stockfish ({self.path}) skill={self.skill_level}"
              + (f" (custom requested {self.custom_skill})" if self.custom_skill else "")
              + f", threads={self.threads}, hash={self.hash_mb}MB")

    # -------------------------
    # Public API (unchanged)
    # -------------------------
    def choose_move(
        self,
        game_state: Any,
        *,
        time_limit: Optional[float] = None,
        depth: Optional[int] = None,
    ) -> Optional[str]:
        board = self._board_from_game_state(game_state)
        return self._choose_move_from_board(board, time_limit=time_limit, depth=depth)

    def get_best_move(
        self,
        fen: str,
        *,
        time_limit: Optional[float] = None,
        depth: Optional[int] = None,
    ) -> Optional[str]:
        try:
            board = chess.Board(fen=fen)
        except Exception:
            return None
        return self._choose_move_from_board(board, time_limit=time_limit, depth=depth)

    # -------------------------
    # Core play
    # -------------------------
    def _choose_move_from_board(
        self,
        board: chess.Board,
        *,
        time_limit: Optional[float] = None,
        depth: Optional[int] = None,
    ) -> Optional[str]:
        if board.is_game_over():
            return None

        use_time = False
        if time_limit is not None:
            use_time = True
        elif depth is None and self.default_time is not None:
            use_time = True
            time_limit = self.default_time
        elif depth is None:
            depth = self.default_depth

        if use_time and (time_limit is None or time_limit <= 0):
            use_time = False
            depth = depth or self.default_depth

        if self._engine is None:
            raise RuntimeError("Stockfish engine process is not running")

        try:
            limit = chess.engine.Limit(time=time_limit) if use_time else chess.engine.Limit(depth=depth)
            result = self._engine.play(board, limit)
            if result is None or result.move is None:
                return None
            return result.move.uci()
        except EngineTerminatedError:
            self._engine = None
            raise RuntimeError("Stockfish terminated unexpectedly")
        except EngineError as ee:
            raise RuntimeError(f"EngineError during play: {ee}") from ee
        except Exception as e:
            print(f"[engine] unexpected error in play: {e}")
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

