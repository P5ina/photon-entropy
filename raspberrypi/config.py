import os
from dataclasses import dataclass


@dataclass
class Config:
    server_url: str = "http://localhost:8080"
    device_id: str = "pi-001"
    collect_interval: int = 30  # seconds between collections
    samples_per_commit: int = 500  # samples per commit
    light_threshold: int = 2000  # ADC value threshold (collect only in dark)
    adc_address: int = 0x48  # ADS1115 I2C address
    adc_channel: int = 0  # ADC channel (A0)
    sample_rate: int = 860  # samples per second
    min_quality: float = 0.5  # minimum quality to submit

    @classmethod
    def from_env(cls) -> "Config":
        return cls(
            server_url=os.getenv("SERVER_URL", cls.server_url),
            device_id=os.getenv("DEVICE_ID", cls.device_id),
            collect_interval=int(os.getenv("COLLECT_INTERVAL", cls.collect_interval)),
            samples_per_commit=int(os.getenv("SAMPLES_PER_COMMIT", cls.samples_per_commit)),
            light_threshold=int(os.getenv("LIGHT_THRESHOLD", cls.light_threshold)),
            adc_address=int(os.getenv("ADC_ADDRESS", cls.adc_address), 16 if os.getenv("ADC_ADDRESS", "").startswith("0x") else 10),
            adc_channel=int(os.getenv("ADC_CHANNEL", cls.adc_channel)),
            sample_rate=int(os.getenv("SAMPLE_RATE", cls.sample_rate)),
            min_quality=float(os.getenv("MIN_QUALITY", cls.min_quality)),
        )
