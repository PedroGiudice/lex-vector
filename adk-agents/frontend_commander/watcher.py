"""
Docker Watcher for Frontend Commander

Monitors Docker events and triggers the Frontend Commander agent
when new backend containers are detected.

Usage:
    python watcher.py              # Run watcher (foreground)
    python watcher.py --daemon     # Run as background daemon
    python watcher.py --once       # Check once and exit
"""
import subprocess
import json
import time
import argparse
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional

# State file to track processed containers
STATE_FILE = Path(__file__).parent / ".processed_containers.json"
LOG_FILE = Path(__file__).parent / "watcher.log"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


class ContainerState:
    """Manages state of processed containers."""

    def __init__(self):
        self.state_file = STATE_FILE
        self.processed: dict = self._load()

    def _load(self) -> dict:
        if self.state_file.exists():
            try:
                return json.loads(self.state_file.read_text())
            except:
                return {}
        return {}

    def _save(self):
        self.state_file.write_text(json.dumps(self.processed, indent=2))

    def is_processed(self, container_id: str) -> bool:
        return container_id in self.processed

    def mark_processed(self, container_id: str, container_name: str):
        self.processed[container_id] = {
            "name": container_name,
            "processed_at": datetime.now().isoformat(),
        }
        self._save()


def get_running_containers() -> list[dict]:
    """Get list of running Docker containers."""
    try:
        result = subprocess.run(
            ["docker", "ps", "--format", "json"],
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode != 0:
            logger.error(f"Docker ps failed: {result.stderr}")
            return []

        containers = []
        for line in result.stdout.strip().split("\n"):
            if line:
                containers.append(json.loads(line))

        return containers

    except subprocess.TimeoutExpired:
        logger.error("Docker command timed out")
        return []
    except Exception as e:
        logger.error(f"Error getting containers: {e}")
        return []


def is_backend_service(container: dict) -> bool:
    """
    Determine if a container is a backend service we should generate UI for.

    Filters:
    - Must have exposed ports (API service)
    - Must not be a database/infrastructure container
    - Must be related to legal-workbench
    """
    name = container.get("Names", "").lower()
    image = container.get("Image", "").lower()
    ports = container.get("Ports", "")

    # Exclude infrastructure containers
    infra_keywords = ["postgres", "redis", "mongo", "mysql", "nginx", "traefik", "prometheus"]
    if any(kw in name or kw in image for kw in infra_keywords):
        return False

    # Must have ports exposed (it's an API)
    if not ports:
        return False

    # Prefer containers with API-like names
    api_keywords = ["api", "service", "backend", "server"]
    if any(kw in name or kw in image for kw in api_keywords):
        return True

    # Accept any container with web ports
    web_ports = ["80", "8000", "8080", "3000", "5000", "8501"]
    if any(port in ports for port in web_ports):
        return True

    return False


def notify_user(container_name: str, message: str):
    """
    Send notification to user about new container.

    TODO: Integrate with actual notification system (Telegram, Slack, etc.)
    For now, just logs to console.
    """
    logger.info(f"\n{'='*60}")
    logger.info(f"NEW BACKEND DETECTED: {container_name}")
    logger.info(f"{'='*60}")
    logger.info(message)
    logger.info(f"{'='*60}\n")

    # Future: Add Telegram/Slack notification
    # from shared.notifier import send_telegram
    # send_telegram(f"🔔 New backend: {container_name}\n{message}")


def trigger_frontend_commander(container: dict) -> bool:
    """
    Trigger the Frontend Commander agent for a new container.

    Returns True if successful, False otherwise.
    """
    container_name = container.get("Names", "unknown")
    container_id = container.get("ID", "unknown")

    logger.info(f"Triggering Frontend Commander for: {container_name}")

    try:
        # Import and run the agent
        # For ADK, we use the adk CLI or programmatic invocation
        from google.adk import Runner
        from .agent import root_agent

        runner = Runner(agent=root_agent)

        # Initial prompt to start the agent
        initial_prompt = f"""
        A new backend service was detected:

        - Container Name: {container_name}
        - Container ID: {container_id}
        - Image: {container.get('Image', 'unknown')}
        - Ports: {container.get('Ports', 'none')}

        Please:
        1. Analyze this service using read_backend_code and get_service_endpoints
        2. Ask the user how they want the UI to look
        3. Generate the appropriate frontend module
        """

        # Run the agent (this will be interactive)
        result = runner.run(initial_prompt)

        logger.info(f"Frontend Commander completed for {container_name}")
        return True

    except ImportError:
        # ADK not installed, fall back to notification only
        logger.warning("ADK not installed. Sending notification only.")
        notify_user(
            container_name,
            f"New backend detected. Run Frontend Commander manually:\n"
            f"cd adk-agents && adk run frontend-commander",
        )
        return True

    except Exception as e:
        logger.error(f"Error running Frontend Commander: {e}")
        return False


def watch_once():
    """Check for new containers once and process them."""
    state = ContainerState()
    containers = get_running_containers()

    new_backends = []
    for container in containers:
        container_id = container.get("ID", "")
        if not state.is_processed(container_id) and is_backend_service(container):
            new_backends.append(container)

    if not new_backends:
        logger.info("No new backend services detected.")
        return

    logger.info(f"Found {len(new_backends)} new backend service(s)")

    for container in new_backends:
        container_id = container.get("ID", "")
        container_name = container.get("Names", "unknown")

        success = trigger_frontend_commander(container)

        if success:
            state.mark_processed(container_id, container_name)
            logger.info(f"Processed: {container_name}")


def watch_continuous(interval: int = 30):
    """
    Continuously watch for new containers.

    Args:
        interval: Seconds between checks
    """
    logger.info(f"Starting continuous watch (interval: {interval}s)")
    logger.info("Press Ctrl+C to stop")

    try:
        while True:
            watch_once()
            time.sleep(interval)
    except KeyboardInterrupt:
        logger.info("Watcher stopped by user")


def watch_docker_events():
    """
    Watch Docker events stream for real-time detection.
    More efficient than polling.
    """
    logger.info("Starting Docker events watcher")
    logger.info("Press Ctrl+C to stop")

    state = ContainerState()

    try:
        process = subprocess.Popen(
            ["docker", "events", "--filter", "event=start", "--format", "json"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        for line in process.stdout:
            if not line.strip():
                continue

            try:
                event = json.loads(line)
                container_id = event.get("id", "")[:12]

                # Get container details
                containers = get_running_containers()
                container = next(
                    (c for c in containers if c.get("ID", "").startswith(container_id)),
                    None,
                )

                if container and not state.is_processed(container_id):
                    if is_backend_service(container):
                        trigger_frontend_commander(container)
                        state.mark_processed(
                            container_id,
                            container.get("Names", "unknown"),
                        )

            except json.JSONDecodeError:
                continue

    except KeyboardInterrupt:
        logger.info("Watcher stopped by user")
        process.terminate()


def main():
    parser = argparse.ArgumentParser(
        description="Watch for new Docker containers and trigger Frontend Commander"
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Check once and exit",
    )
    parser.add_argument(
        "--daemon",
        action="store_true",
        help="Run as background daemon using Docker events",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=30,
        help="Polling interval in seconds (default: 30)",
    )

    args = parser.parse_args()

    if args.once:
        watch_once()
    elif args.daemon:
        watch_docker_events()
    else:
        watch_continuous(args.interval)


if __name__ == "__main__":
    main()
