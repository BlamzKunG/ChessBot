# ChessBot

An advanced Lichess bot integrated with Stockfish, featuring dynamic time management, automated engine discovery, and robust error handling.

## Core Features

### 1. Dynamic Time Management
The engine employs a sophisticated time allocation algorithm that adapts to the current game state:
*   **Disadvantage Recovery:** Automatically increases thinking time by up to 4x when the position evaluation drops significantly, ensuring deep calculation in critical defensive moments.
*   **Complexity Analysis:** Utilizes Multi-PV analysis to identify positions with multiple viable candidates, allocating extra time to resolve tactical ambiguity.
*   **Panic Mode:** Shifts to ultra-fast execution (sub-100ms) when the remaining clock falls below 1.5 seconds to prevent time forfeits.
*   **Safety Guards:** Implements a dynamic ceiling to ensure no single move consumes more than 25% of the remaining time, maintaining a healthy clock buffer.

### 2. Intelligent Engine Integration
*   **Automated Discovery:** Supports cross-platform Stockfish binary detection (Linux/Windows/Android-Termux).
*   **Real-time Configuration:** Dynamically adjusts Skill Level, Threads, and Hash Memory based on environment variables or configuration files.

### 3. Operational Stability
*   **Unified Execution:** All startup, discovery, and game logic are consolidated into a single entry point (`bot.py`).
*   **Latency Compensation:** Configurable move overhead (default 500ms) to account for network jitter and API response times.
*   **Resilient Streams:** Implements automatic reconnection and error handling for Lichess gameState event streams.

## Installation

### Prerequisites
*   Python 3.8+
*   Stockfish binary installed or placed in the project directory.
*   Lichess Personal Access Token (PAT) with "Play as a bot" permissions.

### Setup
1. Clone the repository:
   ```bash
   git clone https://github.com/BlamzKunG/ChessBot.git
   cd ChessBot
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Configure your credentials in `config.py` or set the `TOKEN` environment variable.

## Usage

Start the bot by executing the main script:
```bash
python bot.py
```

## Configuration

Settings can be adjusted in `config.py`:
*   `MOVE_OVERHEAD`: Latency buffer in milliseconds.
*   `MIN_TIME`: Minimum thinking time per move.
*   `MAX_TIME`: Maximum thinking time per move.
*   `DEFAULT_DEPTH`: Search depth used when time parameters are unavailable.

## License
MIT License
