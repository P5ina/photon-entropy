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
        adc_addr_env = os.getenv("ADC_ADDRESS")
        if adc_addr_env:
            adc_address = int(adc_addr_env, 16) if adc_addr_env.startswith("0x") else int(adc_addr_env)
        else:
            adc_address = cls.adc_address

        return cls(
            server_url=os.getenv("SERVER_URL", cls.server_url),
            device_id=os.getenv("DEVICE_ID", cls.device_id),
            collect_interval=int(os.getenv("COLLECT_INTERVAL", str(cls.collect_interval))),
            samples_per_commit=int(os.getenv("SAMPLES_PER_COMMIT", str(cls.samples_per_commit))),
            light_threshold=int(os.getenv("LIGHT_THRESHOLD", str(cls.light_threshold))),
            adc_address=adc_address,
            adc_channel=int(os.getenv("ADC_CHANNEL", str(cls.adc_channel))),
            sample_rate=int(os.getenv("SAMPLE_RATE", str(cls.sample_rate))),
            min_quality=float(os.getenv("MIN_QUALITY", str(cls.min_quality))),
        )
