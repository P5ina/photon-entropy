"""Configuration for Bomb Defusal game."""
import os
from dataclasses import dataclass


@dataclass
class Config:
    """Game configuration."""

    # Server settings
    server_url: str = "wss://entropy.p5ina.dev/ws"
    api_url: str = "https://entropy.p5ina.dev"
    device_id: str = "bomb-001"

    # GPIO pins - Wires module (4 buttons + 4 LEDs)
    # Buttons use internal pull-up: GPIO -> Button -> GND (no external resistor)
    wire_buttons: tuple = (19, 26, 21, 15)  # Button 4 on GPIO 15 (Pin 10)
    wire_leds: tuple = (25, 8, 7, 1)

    # GPIO pins - Keypad module (rotary encoder)
    rotary_clk: int = 5
    rotary_dt: int = 6
    rotary_sw: int = 13

    # GPIO pins - Simon module (RGB LED + touch)
    rgb_red: int = 17
    rgb_green: int = 27
    rgb_blue: int = 22
    touch_pin: int = 12

    # GPIO pins - Magnet module (Hall sensor)
    hall_pin: int = 16

    # GPIO pins - Output
    buzzer_pin: int = 18

    # I2C settings (LCD)
    lcd_address: int = 0x27  # Common addresses: 0x27 or 0x3F
    lcd_cols: int = 16
    lcd_rows: int = 2

    # Game settings
    debug: bool = False
    mock_hardware: bool = False

    @classmethod
    def from_env(cls) -> "Config":
        """Load configuration from environment variables."""
        lcd_addr_env = os.getenv("LCD_ADDRESS")
        if lcd_addr_env:
            lcd_address = int(lcd_addr_env, 16) if lcd_addr_env.startswith("0x") else int(lcd_addr_env)
        else:
            lcd_address = cls.lcd_address

        return cls(
            server_url=os.getenv("SERVER_URL", cls.server_url),
            api_url=os.getenv("API_URL", cls.api_url),
            device_id=os.getenv("DEVICE_ID", cls.device_id),
            lcd_address=lcd_address,
            debug=os.getenv("DEBUG", "false").lower() == "true",
            mock_hardware=os.getenv("MOCK_HARDWARE", "false").lower() == "true",
        )
