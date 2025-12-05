#!/usr/bin/env python3
import argparse
import logging
import signal
import sys
import time
from typing import Optional

from dotenv import load_dotenv
load_dotenv()

from config import Config
from entropy_collector import EntropyCollector
from entropy_tester import EntropyTester
from api_client import APIClient

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("photon-entropy")

running = True


def signal_handler(signum, frame):
    global running
    logger.info("Shutdown signal received")
    running = False


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="PhotonEntropy IoT Client - Collects entropy from photoresistor"
    )
    parser.add_argument(
        "--server",
        type=str,
        help="Backend server URL (default: http://localhost:8080)",
    )
    parser.add_argument(
        "--device-id",
        type=str,
        help="Device ID (default: pi-001)",
    )
    parser.add_argument(
        "--interval",
        type=int,
        help="Collection interval in seconds (default: 30)",
    )
    parser.add_argument(
        "--samples",
        type=int,
        help="Number of samples per commit (default: 500)",
    )
    parser.add_argument(
        "--skip-darkness-check",
        action="store_true",
        help="Skip waiting for darkness before collecting",
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run once and exit (useful for testing)",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging",
    )
    return parser.parse_args()


def main():
    global running

    args = parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    config = Config.from_env()

    if args.server:
        config.server_url = args.server
    if args.device_id:
        config.device_id = args.device_id
    if args.interval:
        config.collect_interval = args.interval
    if args.samples:
        config.samples_per_commit = args.samples

    logger.info(f"PhotonEntropy IoT Client starting")
    logger.info(f"  Device ID: {config.device_id}")
    logger.info(f"  Server: {config.server_url}")
    logger.info(f"  Samples per commit: {config.samples_per_commit}")
    logger.info(f"  Collect interval: {config.collect_interval}s")

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    collector = EntropyCollector(config)
    tester = EntropyTester()
    client = APIClient(config)

    if not client.health_check():
        logger.error(f"Cannot connect to server at {config.server_url}")
        sys.exit(1)

    logger.info("Connected to server successfully")

    while running:
        try:
            if not args.skip_darkness_check:
                if not collector.wait_for_darkness(timeout=config.collect_interval):
                    logger.info("Still too bright, skipping this cycle")
                    if args.once:
                        break
                    continue

            samples, timestamps = collector.collect()

            results = tester.test(samples)
            logger.info(f"Local quality check: {results.quality:.0%}")
            logger.info(f"  Frequency: {'PASS' if results.frequency.passed else 'FAIL'} ({results.frequency.value:.4f})")
            logger.info(f"  Runs: {'PASS' if results.runs.passed else 'FAIL'} (max={results.runs.value:.0f})")
            logger.info(f"  Chi-Square: {'PASS' if results.chi_square.passed else 'FAIL'} ({results.chi_square.value:.4f})")
            logger.info(f"  Variance: {'PASS' if results.variance.passed else 'FAIL'} ({results.variance.value:.4f})")

            if results.quality < config.min_quality:
                logger.warning(f"Quality {results.quality:.0%} below threshold {config.min_quality:.0%}, skipping submit")
                if args.once:
                    break
                time.sleep(config.collect_interval)
                continue

            response = client.submit(samples, timestamps)

            if response:
                logger.info(f"Server response: quality={response.quality:.0%}, accepted={response.accepted}")
            else:
                logger.error("Failed to submit samples to server")

            if args.once:
                break

            logger.info(f"Sleeping for {config.collect_interval}s...")
            for _ in range(config.collect_interval):
                if not running:
                    break
                time.sleep(1)

        except Exception as e:
            logger.exception(f"Error in main loop: {e}")
            if args.once:
                break
            time.sleep(10)

    logger.info("PhotonEntropy IoT Client stopped")


if __name__ == "__main__":
    main()
