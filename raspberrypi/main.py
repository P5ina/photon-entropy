#!/usr/bin/env python3
"""Bomb Defusal Game - Raspberry Pi Controller."""
import asyncio
import signal
import sys
import argparse

from dotenv import load_dotenv

from config import Config
from game_controller import GameController


# Load environment variables
load_dotenv()


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Bomb Defusal Game Controller")
    parser.add_argument("--mock", action="store_true", help="Run in mock hardware mode")
    parser.add_argument("--game-id", type=str, help="Game ID to join")
    parser.add_argument("--server", type=str, help="Server URL override")
    args = parser.parse_args()

    # Load configuration
    config = Config.from_env()

    if args.mock:
        config.mock_hardware = True
    if args.server:
        config.server_url = args.server

    print("=" * 50)
    print("   BOMB DEFUSAL GAME CONTROLLER")
    print("=" * 50)
    print(f"Server: {config.server_url}")
    print(f"Device: {config.device_id}")
    print(f"Mock: {config.mock_hardware}")
    print("=" * 50)

    # Create game controller
    controller = GameController(config)

    # Handle shutdown
    shutdown_event = asyncio.Event()

    def handle_shutdown(sig, frame):
        print("\n[Main] Shutting down...")
        shutdown_event.set()

    signal.signal(signal.SIGINT, handle_shutdown)
    signal.signal(signal.SIGTERM, handle_shutdown)

    try:
        # Initialize hardware
        controller.setup()

        # Connect to server
        await controller.connect(config.server_url)

        # Create or join game
        if args.game_id:
            await controller.join_game(args.game_id)
        else:
            # Create a new game and display code on LCD
            await controller.create_game()

        # Run game loop
        print("[Main] Starting game loop...")

        # Create tasks
        game_task = asyncio.create_task(controller.run())
        shutdown_task = asyncio.create_task(shutdown_event.wait())

        # Wait for either game to end or shutdown
        done, pending = await asyncio.wait(
            [game_task, shutdown_task],
            return_when=asyncio.FIRST_COMPLETED
        )

        # Cancel pending tasks
        for task in pending:
            task.cancel()

    except KeyboardInterrupt:
        print("\n[Main] Interrupted")
    except Exception as e:
        print(f"[Main] Error: {e}")
        raise
    finally:
        controller.cleanup()
        print("[Main] Goodbye!")


def run_demo():
    """Run a demo without server connection."""
    print("=" * 50)
    print("   BOMB DEFUSAL DEMO MODE")
    print("=" * 50)

    config = Config.from_env()
    config.mock_hardware = True

    controller = GameController(config)
    controller.setup()

    print("\nDemo: Simulating game actions...")
    print("-" * 30)

    # Simulate game start with more strikes allowed
    controller._on_game_started({
        "game_id": "demo-001",
        "time_limit": 120,
        "max_strikes": 10,  # Allow more mistakes for demo
        "modules": {
            "wires": {"wire_order": [1, 3, 0]},
            "keypad": {"code": [4, 2, 7]},
            "simon": {"sequence": ["red", "blue", "green"], "rounds": 2},
            "magnet": {"safe_zones": [(5, 10)], "required": 1},
            "stability": {"max_tilts": 5, "stable_duration": 10},
        }
    })

    print("\n--- Testing Wires Module ---")
    controller.wires.simulate_cut(1)  # Correct (blue)
    controller.wires.simulate_cut(3)  # Correct (orange)
    controller.wires.simulate_cut(0)  # Correct (red) - solved!

    print("\n--- Testing Keypad Module ---")
    # Enter code: 4, 2, 7
    for _ in range(4):
        controller.keypad.simulate_rotate(1)  # Go to 4
    controller.keypad.simulate_confirm()  # 4 - correct

    for _ in range(2):
        controller.keypad.simulate_rotate(1)  # Go to 2 (from 0)
    controller.keypad.simulate_confirm()  # 2 - correct

    for _ in range(7):
        controller.keypad.simulate_rotate(1)  # Go to 7 (from 0)
    controller.keypad.simulate_confirm()  # 7 - correct - solved!

    print("\n--- Cleanup ---")
    controller.cleanup()
    print("Demo complete!")


if __name__ == "__main__":
    if "--demo" in sys.argv:
        run_demo()
    else:
        asyncio.run(main())
