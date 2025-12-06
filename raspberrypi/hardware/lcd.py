"""LCD 16x2 I2C display driver."""
import time
from typing import Optional

try:
    from RPLCD.i2c import CharLCD
    HAS_RPLCD = True
except ImportError:
    HAS_RPLCD = False


class LCD:
    """16x2 I2C LCD display controller."""

    def __init__(self, address: int = 0x27, cols: int = 16, rows: int = 2, mock: bool = False):
        self.address = address
        self.cols = cols
        self.rows = rows
        self.mock = mock or not HAS_RPLCD
        self._lcd: Optional[CharLCD] = None
        self._current_lines = ["", ""]

    def setup(self):
        """Initialize the LCD."""
        if self.mock:
            print(f"[LCD] Mock mode - address 0x{self.address:02X}")
            return

        try:
            self._lcd = CharLCD(
                i2c_expander='PCF8574',
                address=self.address,
                port=1,
                cols=self.cols,
                rows=self.rows,
                dotsize=8,
                charmap='A02',
                auto_linebreaks=True,
            )
            self._lcd.clear()
        except Exception as e:
            print(f"[LCD] Failed to initialize: {e}")
            self.mock = True

    def clear(self):
        """Clear the display."""
        self._current_lines = ["", ""]
        if self.mock:
            print("[LCD] ----------------")
            print("[LCD] |              |")
            print("[LCD] |              |")
            print("[LCD] ----------------")
            return

        if self._lcd:
            self._lcd.clear()

    def write(self, line1: str, line2: str = ""):
        """Write text to both lines."""
        # Pad/truncate to LCD width
        line1 = line1[:self.cols].ljust(self.cols)
        line2 = line2[:self.cols].ljust(self.cols)

        self._current_lines = [line1, line2]

        if self.mock:
            print(f"[LCD] |{line1}|")
            print(f"[LCD] |{line2}|")
            return

        if self._lcd:
            self._lcd.cursor_pos = (0, 0)
            self._lcd.write_string(line1)
            self._lcd.cursor_pos = (1, 0)
            self._lcd.write_string(line2)

    def write_line(self, line: int, text: str):
        """Write text to a specific line (0 or 1)."""
        if line not in (0, 1):
            return

        text = text[:self.cols].ljust(self.cols)
        self._current_lines[line] = text

        if self.mock:
            if line == 0:
                print(f"[LCD] |{text}|")
            else:
                print(f"[LCD] |{text}|")
            return

        if self._lcd:
            self._lcd.cursor_pos = (line, 0)
            self._lcd.write_string(text)

    def show_timer(self, seconds: int, strikes: int = 0):
        """Display timer in MM:SS format with strikes."""
        minutes = seconds // 60
        secs = seconds % 60
        strike_str = "X" * strikes if strikes > 0 else ""
        # Format: "05:30    XXX" (timer left, strikes right)
        timer_str = f"{minutes:02d}:{secs:02d}"
        line = f"{timer_str}{'':>{self.cols - len(timer_str) - len(strike_str)}}{strike_str}"
        self.write_line(0, line)

    def show_strikes(self, strikes: int, max_strikes: int):
        """Display strike counter."""
        strike_display = "X" * strikes + "O" * (max_strikes - strikes)
        self.write_line(1, f"STRIKES: {strike_display}")

    def show_module(self, module_name: str):
        """Display current active module name."""
        # Module names: wires, simon, magnet
        display_names = {
            "wires": ">> WIRES",
            "simon": ">> SIMON",
            "magnet": ">> MAGNET",
        }
        display = display_names.get(module_name, f">> {module_name.upper()}")
        self.write_line(1, display)

    def show_game_state(self, time_left: int, strikes: int, max_strikes: int):
        """Display full game state."""
        minutes = time_left // 60
        secs = time_left % 60
        strike_display = "X" * strikes + "O" * (max_strikes - strikes)
        self.write(
            f"TIME: {minutes:02d}:{secs:02d}",
            f"STRIKES: {strike_display}"
        )

    def show_message(self, line1: str, line2: str = "", duration: float = 2.0):
        """Show a temporary message."""
        old_lines = self._current_lines.copy()
        self.write(line1, line2)
        time.sleep(duration)
        self.write(old_lines[0], old_lines[1])

    def show_win(self):
        """Display win message."""
        self.write("*** DEFUSED! ***", "   YOU WIN!    ")

    def show_lose(self):
        """Display lose message."""
        self.write("*** BOOM!!! ***", "  GAME OVER   ")

    def show_explosion(self):
        """Display explosion animation."""
        self.write("*** BOOM!!! ***", "  GAME OVER   ")
        if self.mock:
            print("[LCD] |*** BOOM!!! ***|")
            print("[LCD] |  GAME OVER    |")

    def cleanup(self):
        """Clean up the LCD."""
        if self._lcd:
            self._lcd.clear()
            self._lcd.close()
