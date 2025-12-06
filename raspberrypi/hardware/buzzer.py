"""Buzzer driver for sound effects using gpiozero (Pi 5 compatible)."""
import time
import threading
from typing import Optional

try:
    from gpiozero import TonalBuzzer, DigitalOutputDevice
    HAS_GPIO = True
except ImportError:
    HAS_GPIO = False


class Buzzer:
    """Active buzzer controller with sound patterns."""

    def __init__(self, pin: int, mock: bool = False):
        self.pin = pin
        self.mock = mock or not HAS_GPIO
        self._ticking = False
        self._tick_thread: Optional[threading.Thread] = None
        self._stop_tick = threading.Event()
        self._buzzer: Optional[DigitalOutputDevice] = None

    def setup(self):
        """Initialize the buzzer GPIO."""
        if self.mock:
            print(f"[Buzzer] Mock mode - pin {self.pin}")
            return

        # Use DigitalOutputDevice for active buzzer (just on/off)
        self._buzzer = DigitalOutputDevice(self.pin)

    def beep(self, duration: float = 0.1):
        """Single beep."""
        if self.mock:
            print(f"[Buzzer] BEEP ({duration}s)")
            return

        if self._buzzer:
            self._buzzer.on()
            time.sleep(duration)
            self._buzzer.off()

    def tick(self):
        """Single short tick sound."""
        self.beep(0.02)

    def play_pattern(self, pattern_name: str):
        """Play a named sound pattern."""
        patterns = {
            "tick": lambda: self.tick(),
            "error": lambda: self.error_sound(),
            "success": lambda: self.success_sound(),
            "win": lambda: self.win_sound(),
            "explosion": lambda: self.explosion_sound(),
        }
        if pattern_name in patterns:
            patterns[pattern_name]()

    def beep_pattern(self, pattern: list[tuple[float, float]]):
        """Play a beep pattern: list of (on_time, off_time) tuples."""
        for on_time, off_time in pattern:
            self.beep(on_time)
            time.sleep(off_time)

    def error_sound(self):
        """Play error/strike sound."""
        self.beep_pattern([
            (0.2, 0.1),
            (0.2, 0.1),
            (0.4, 0),
        ])

    def success_sound(self):
        """Play success/solved sound."""
        self.beep_pattern([
            (0.1, 0.05),
            (0.1, 0.05),
            (0.1, 0),
        ])

    def win_sound(self):
        """Play victory sound."""
        self.beep_pattern([
            (0.1, 0.1),
            (0.1, 0.1),
            (0.1, 0.1),
            (0.3, 0),
        ])

    def explosion_sound(self):
        """Play explosion sound."""
        if self.mock:
            print("[Buzzer] BOOM! (explosion)")
            return

        # Long beep that gets louder (simulated by rapid on/off)
        for _ in range(10):
            self.beep(0.1)
            time.sleep(0.02)
        self.beep(0.5)

    def start_ticking(self, interval: float = 1.0):
        """Start ticking sound in background."""
        if self._ticking:
            return

        self._ticking = True
        self._stop_tick.clear()
        self._tick_thread = threading.Thread(target=self._tick_loop, args=(interval,))
        self._tick_thread.daemon = True
        self._tick_thread.start()

    def _tick_loop(self, interval: float):
        """Background tick loop."""
        while not self._stop_tick.is_set():
            self.beep(0.02)
            self._stop_tick.wait(interval)

    def stop_ticking(self):
        """Stop ticking sound."""
        self._ticking = False
        self._stop_tick.set()
        if self._tick_thread:
            self._tick_thread.join(timeout=1)
            self._tick_thread = None

    def set_tick_speed(self, interval: float):
        """Change tick speed (restart with new interval)."""
        if self._ticking:
            self.stop_ticking()
            self.start_ticking(interval)

    def on(self):
        """Turn buzzer on continuously."""
        if self.mock:
            print("[Buzzer] ON")
            return
        if self._buzzer:
            self._buzzer.on()

    def off(self):
        """Turn buzzer off."""
        if self.mock:
            print("[Buzzer] OFF")
            return
        if self._buzzer:
            self._buzzer.off()

    def cleanup(self):
        """Clean up resources."""
        self.stop_ticking()
        if self._buzzer:
            self._buzzer.off()
            self._buzzer.close()
            self._buzzer = None
