"""RGB LED driver."""
import time
import threading
from typing import Optional, Tuple

try:
    import RPi.GPIO as GPIO
    HAS_GPIO = True
except ImportError:
    HAS_GPIO = False


class RGBLED:
    """RGB LED controller with color mixing."""

    # Predefined colors
    COLORS = {
        "off": (0, 0, 0),
        "red": (255, 0, 0),
        "green": (0, 255, 0),
        "blue": (0, 0, 255),
        "yellow": (255, 255, 0),
        "cyan": (0, 255, 255),
        "magenta": (255, 0, 255),
        "white": (255, 255, 255),
        "orange": (255, 128, 0),
    }

    def __init__(self, red_pin: int, green_pin: int, blue_pin: int, mock: bool = False):
        self.red_pin = red_pin
        self.green_pin = green_pin
        self.blue_pin = blue_pin
        self.mock = mock or not HAS_GPIO
        self._pwm_r: Optional[GPIO.PWM] = None
        self._pwm_g: Optional[GPIO.PWM] = None
        self._pwm_b: Optional[GPIO.PWM] = None
        self._current_color = "off"
        self._blinking = False
        self._blink_thread: Optional[threading.Thread] = None
        self._stop_blink = threading.Event()

    def setup(self):
        """Initialize RGB LED GPIO with PWM."""
        if self.mock:
            print(f"[RGB LED] Mock mode - R:{self.red_pin} G:{self.green_pin} B:{self.blue_pin}")
            return

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.red_pin, GPIO.OUT)
        GPIO.setup(self.green_pin, GPIO.OUT)
        GPIO.setup(self.blue_pin, GPIO.OUT)

        # Setup PWM at 1000Hz
        self._pwm_r = GPIO.PWM(self.red_pin, 1000)
        self._pwm_g = GPIO.PWM(self.green_pin, 1000)
        self._pwm_b = GPIO.PWM(self.blue_pin, 1000)

        self._pwm_r.start(0)
        self._pwm_g.start(0)
        self._pwm_b.start(0)

    def set_rgb(self, r: int, g: int, b: int):
        """Set RGB values (0-255 each)."""
        if self.mock:
            print(f"[RGB LED] RGB({r}, {g}, {b})")
            return

        # Convert 0-255 to 0-100 duty cycle
        self._pwm_r.ChangeDutyCycle(r * 100 / 255)
        self._pwm_g.ChangeDutyCycle(g * 100 / 255)
        self._pwm_b.ChangeDutyCycle(b * 100 / 255)

    def set_color(self, color: str):
        """Set color by name."""
        self._current_color = color
        if color in self.COLORS:
            r, g, b = self.COLORS[color]
            self.set_rgb(r, g, b)
        else:
            self.off()

    def get_color(self) -> str:
        """Get current color name."""
        return self._current_color

    def off(self):
        """Turn off the LED."""
        self._current_color = "off"
        self.set_rgb(0, 0, 0)

    def red(self):
        """Set to red."""
        self.set_color("red")

    def green(self):
        """Set to green."""
        self.set_color("green")

    def blue(self):
        """Set to blue."""
        self.set_color("blue")

    def start_blinking(self, color: str, interval: float = 0.5):
        """Start blinking in background."""
        if self._blinking:
            self.stop_blinking()

        self._blinking = True
        self._stop_blink.clear()
        self._blink_thread = threading.Thread(
            target=self._blink_loop,
            args=(color, interval)
        )
        self._blink_thread.daemon = True
        self._blink_thread.start()

    def _blink_loop(self, color: str, interval: float):
        """Background blink loop."""
        while not self._stop_blink.is_set():
            self.set_color(color)
            self._stop_blink.wait(interval)
            if not self._stop_blink.is_set():
                self.off()
                self._stop_blink.wait(interval)

    def stop_blinking(self):
        """Stop blinking."""
        self._blinking = False
        self._stop_blink.set()
        if self._blink_thread:
            self._blink_thread.join(timeout=1)
            self._blink_thread = None

    def flash(self, color: str, duration: float = 0.2):
        """Flash a color briefly."""
        old_color = self._current_color
        self.set_color(color)
        time.sleep(duration)
        self.set_color(old_color)

    def show_sequence(self, colors: list[str], duration: float = 0.5, pause: float = 0.3):
        """Show a sequence of colors."""
        for color in colors:
            self.set_color(color)
            time.sleep(duration)
            self.off()
            time.sleep(pause)

    def cleanup(self):
        """Clean up resources."""
        self.stop_blinking()
        self.off()
        if self._pwm_r:
            self._pwm_r.stop()
        if self._pwm_g:
            self._pwm_g.stop()
        if self._pwm_b:
            self._pwm_b.stop()
