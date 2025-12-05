import logging
from dataclasses import dataclass
from typing import List, Optional

import requests

from config import Config

logger = logging.getLogger(__name__)


@dataclass
class SubmitResponse:
    id: str
    quality: float
    accepted: bool
    tests: dict


class APIClient:
    def __init__(self, config: Config):
        self.config = config
        self.base_url = config.server_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "User-Agent": f"PhotonEntropy-IoT/{config.device_id}",
        })

    def health_check(self) -> bool:
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=5)
            return response.status_code == 200
        except requests.RequestException as e:
            logger.error(f"Health check failed: {e}")
            return False

    def submit(
        self,
        raw_samples: List[int],
        timestamps: List[int],
        is_too_bright: bool = False,
    ) -> Optional[SubmitResponse]:
        try:
            payload = {
                "device_id": self.config.device_id,
                "raw_samples": raw_samples,
                "timestamps": timestamps,
                "is_too_bright": is_too_bright,
            }

            logger.debug(f"Submitting {len(raw_samples)} samples to {self.base_url}")

            response = self.session.post(
                f"{self.base_url}/api/v1/entropy/submit",
                json=payload,
                timeout=30,
            )

            if response.status_code == 200:
                data = response.json()
                result = SubmitResponse(
                    id=data["id"],
                    quality=data["quality"],
                    accepted=data["accepted"],
                    tests=data.get("tests", {}),
                )
                logger.info(f"Submit successful: id={result.id}, quality={result.quality:.0%}, accepted={result.accepted}")
                return result
            else:
                logger.error(f"Submit failed: {response.status_code} - {response.text}")
                return None

        except requests.RequestException as e:
            logger.error(f"Submit request failed: {e}")
            return None

    def get_status(self) -> Optional[dict]:
        try:
            response = self.session.get(
                f"{self.base_url}/api/v1/device/status",
                params={"device_id": self.config.device_id},
                timeout=10,
            )

            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Get status failed: {response.status_code}")
                return None

        except requests.RequestException as e:
            logger.error(f"Get status request failed: {e}")
            return None

    def report_status(self, is_too_bright: bool) -> bool:
        try:
            payload = {
                "device_id": self.config.device_id,
                "is_too_bright": is_too_bright,
            }

            response = self.session.post(
                f"{self.base_url}/api/v1/device/status",
                json=payload,
                timeout=10,
            )

            if response.status_code == 200:
                logger.debug(f"Status reported: is_too_bright={is_too_bright}")
                return True
            else:
                logger.error(f"Report status failed: {response.status_code}")
                return False

        except requests.RequestException as e:
            logger.error(f"Report status request failed: {e}")
            return False
