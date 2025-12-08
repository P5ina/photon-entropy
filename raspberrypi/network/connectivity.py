"""Network connectivity utilities."""
import socket
import time
from typing import Optional, Callable
from urllib.parse import urlparse


def check_internet_connection(host: str = "8.8.8.8", port: int = 53, timeout: float = 3.0) -> bool:
    """
    Check if there's an internet connection by trying to connect to a DNS server.

    Args:
        host: Host to connect to (default: Google DNS)
        port: Port to connect to (default: DNS port 53)
        timeout: Connection timeout in seconds

    Returns:
        True if connected, False otherwise
    """
    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
        return True
    except (socket.error, OSError):
        return False


def check_server_reachable(server_url: str, timeout: float = 5.0) -> bool:
    """
    Check if the game server is reachable.

    Args:
        server_url: WebSocket or HTTP URL of the server
        timeout: Connection timeout in seconds

    Returns:
        True if server is reachable, False otherwise
    """
    try:
        # Parse URL to get host and port
        parsed = urlparse(server_url)
        host = parsed.hostname

        # Determine port based on scheme
        if parsed.port:
            port = parsed.port
        elif parsed.scheme in ("wss", "https"):
            port = 443
        else:
            port = 80

        socket.setdefaulttimeout(timeout)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except (socket.error, OSError, Exception) as e:
        print(f"[Network] Server check failed: {e}")
        return False


def wait_for_connection(
    server_url: str,
    on_waiting: Optional[Callable[[int], None]] = None,
    on_connected: Optional[Callable[[], None]] = None,
    check_interval: float = 5.0,
    max_attempts: Optional[int] = None
) -> bool:
    """
    Wait for network connection to become available.

    Args:
        server_url: Server URL to check
        on_waiting: Callback called each attempt with attempt number
        on_connected: Callback called when connection is established
        check_interval: Seconds between connection attempts
        max_attempts: Maximum attempts (None for infinite)

    Returns:
        True if connected, False if max_attempts reached
    """
    attempt = 0

    while True:
        attempt += 1

        # First check general internet connectivity
        if not check_internet_connection():
            print(f"[Network] No internet connection (attempt {attempt})")
            if on_waiting:
                on_waiting(attempt)

            if max_attempts and attempt >= max_attempts:
                return False

            time.sleep(check_interval)
            continue

        # Then check if server is reachable
        if check_server_reachable(server_url):
            print("[Network] Connection established!")
            if on_connected:
                on_connected()
            return True

        print(f"[Network] Server unreachable (attempt {attempt})")
        if on_waiting:
            on_waiting(attempt)

        if max_attempts and attempt >= max_attempts:
            return False

        time.sleep(check_interval)


async def wait_for_connection_async(
    server_url: str,
    on_waiting: Optional[Callable[[int], None]] = None,
    on_connected: Optional[Callable[[], None]] = None,
    check_interval: float = 5.0,
    max_attempts: Optional[int] = None
) -> bool:
    """
    Async version of wait_for_connection.

    Args:
        server_url: Server URL to check
        on_waiting: Callback called each attempt with attempt number
        on_connected: Callback called when connection is established
        check_interval: Seconds between connection attempts
        max_attempts: Maximum attempts (None for infinite)

    Returns:
        True if connected, False if max_attempts reached
    """
    import asyncio

    attempt = 0

    while True:
        attempt += 1

        # Run blocking checks in executor to not block event loop
        loop = asyncio.get_event_loop()

        # Check internet connectivity
        has_internet = await loop.run_in_executor(None, check_internet_connection)
        if not has_internet:
            print(f"[Network] No internet connection (attempt {attempt})")
            if on_waiting:
                on_waiting(attempt)

            if max_attempts and attempt >= max_attempts:
                return False

            await asyncio.sleep(check_interval)
            continue

        # Check server reachability
        server_reachable = await loop.run_in_executor(
            None,
            lambda: check_server_reachable(server_url)
        )

        if server_reachable:
            print("[Network] Connection established!")
            if on_connected:
                on_connected()
            return True

        print(f"[Network] Server unreachable (attempt {attempt})")
        if on_waiting:
            on_waiting(attempt)

        if max_attempts and attempt >= max_attempts:
            return False

        await asyncio.sleep(check_interval)
