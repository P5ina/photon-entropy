import time
import logging
from typing import Tuple, List, Optional

try:
    import board
    import busio
    import adafruit_ads1x15.ads1115 as ADS
    from adafruit_ads1x15.analog_in import AnalogIn
    HAS_HARDWARE = True
except ImportError:
    HAS_HARDWARE = False

from config import Config

logger = logging.getLogger(__name__)


class EntropyCollector:
    def __init__(self, config: Config):
        self.config = config
        self.adc: Optional[object] = None
        self.channel: Optional[object] = None

        if HAS_HARDWARE:
            self._init_hardware()
        else:
            logger.warning("Hardware not available, running in simulation mode")

    def _init_hardware(self) -> None:
        try:
            i2c = busio.I2C(board.SCL, board.SDA)
            self.adc = ADS.ADS1115(i2c, address=self.config.adc_address)
            self.adc.data_rate = self.config.sample_rate

            self.channel = AnalogIn(self.adc, self.config.adc_channel)

            logger.info(f"ADC initialized at address 0x{self.config.adc_address:02x}, channel {self.config.adc_channel}")
        except Exception as e:
            logger.error(f"Failed to initialize ADC: {e}")
            self.adc = None
            self.channel = None

    def read_sample(self) -> int:
        if self.channel is not None:
            return self.channel.value
        else:
            import random
            return random.randint(0, 65535)

    def is_dark(self) -> bool:
        sample = self.read_sample()
        # Higher raw value = darker (inverted logic)
        is_dark = sample > self.config.light_threshold
        logger.debug(f"Light level: {sample}, threshold: {self.config.light_threshold}, is_dark: {is_dark}")
        return is_dark

    def collect(self, num_samples: Optional[int] = None) -> Tuple[List[int], List[int]]:
        if num_samples is None:
            num_samples = self.config.samples_per_commit

        samples: List[int] = []
        timestamps: List[int] = []

        logger.info(f"Collecting {num_samples} samples...")

        start_time = time.time()

        for i in range(num_samples):
            sample = self.read_sample()
            timestamp = int(time.time() * 1000)

            samples.append(sample)
            timestamps.append(timestamp)

            if i % 100 == 0 and i > 0:
                logger.debug(f"Collected {i}/{num_samples} samples")

            # Small delay to avoid overwhelming the ADC
            time.sleep(1.0 / self.config.sample_rate)

        elapsed = time.time() - start_time
        actual_rate = num_samples / elapsed if elapsed > 0 else 0

        logger.info(f"Collected {num_samples} samples in {elapsed:.2f}s ({actual_rate:.1f} samples/sec)")

        return samples, timestamps

    def wait_for_darkness(self, timeout: int = 60) -> bool:
        logger.info("Waiting for darkness...")
        start = time.time()

        while time.time() - start < timeout:
            if self.is_dark():
                logger.info("Darkness detected, ready to collect")
                return True
            time.sleep(1)

        logger.warning(f"Timeout waiting for darkness after {timeout}s")
        return False
