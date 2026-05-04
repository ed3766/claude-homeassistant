#!/usr/bin/env python3
"""Home Assistant Configuration Reload Tool.

Calls the Home Assistant API to reload core configuration after config files
have been pushed to the instance.
"""

import os
import subprocess
import sys
from pathlib import Path


def load_env_file():
    """Load environment variables from .env file."""
    env_file = Path(".env")
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    os.environ[key.strip()] = value.strip().strip('"').strip("'")


def reload_config():
    """Reload Home Assistant core configuration via API."""
    load_env_file()

    ha_url = os.getenv("HA_URL", "http://homeassistant.local:8123")
    token = os.getenv("HA_TOKEN", "")

    if not token:
        print("❌ Error: HA_TOKEN not found in environment or .env file")
        print("   Create a .env file with: HA_TOKEN=your_long_lived_access_token")
        print("   Get your token from Home Assistant Profile page")
        return False

    url = f"{ha_url}/api/services/homeassistant/reload_core_config"

    print("🔄 Reloading Home Assistant core configuration...")
    result = subprocess.run(
        [
            "curl", "-s", "-o", "/dev/null", "-w", "%{http_code}",
            "-X", "POST", url,
            "-H", f"Authorization: Bearer {token}",
            "-H", "Content-Type: application/json",
            "--connect-timeout", "10",
            "--max-time", "30",
        ],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        print(f"❌ Connection error: Cannot reach Home Assistant at {ha_url}")
        print("   Check that Home Assistant is running and accessible")
        return False

    status_code = result.stdout.strip()
    if status_code == "200":
        print("✅ Configuration reloaded successfully!")
        return True
    elif status_code == "401":
        print("❌ Unauthorized: HA_TOKEN is invalid or expired")
        return False
    else:
        print(f"❌ Failed to reload configuration: HTTP {status_code}")
        return False


if __name__ == "__main__":
    SUCCESS = reload_config()
    sys.exit(0 if SUCCESS else 1)
