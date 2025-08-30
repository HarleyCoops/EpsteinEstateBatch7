#!/usr/bin/env python3
"""
PDFTranslator: Extract text from PDFs/images in the original language, then translate to English.

Configuration driven: uses config.yaml for defaults and .env for environment variables.
"""

import sys
import argparse
from pathlib import Path

import yaml
from dotenv import load_dotenv


def load_config(path: Path) -> dict:
    """Load YAML configuration from the given path."""
    with path.open("r") as f:
        return yaml.safe_load(f)


def main():
    # Load environment variables from .env (if present)
    load_dotenv()

    parser = argparse.ArgumentParser(
        description="Extract and translate PDFs or images to English (two-step pipeline)."
    )
    parser.add_argument(
        "-c", "--config",
        type=Path,
        default=Path(__file__).parent / "config.yaml",
        help="Path to YAML config file."
    )
    args = parser.parse_args()

    config_path = args.config
    if not config_path.exists():
        sys.exit(f"Config file not found: {config_path}")

    config = load_config(config_path)

    print(f"Loaded config from {config_path}")
    # TODO: implement extraction and translation pipeline using config values
    # Example access: config["input"]["formats"], config["ocr"]["engine"], etc.

    # Start character intelligence agent monitor if enabled
    agent_cfg = config.get("agent", {})
    if agent_cfg.get("enabled"):
        try:
            from agent_monitor import start_agent_monitor
            import threading

            threading.Thread(
                target=start_agent_monitor,
                args=(agent_cfg,),
                daemon=True,
            ).start()
        except ImportError:
            print(
                "Agent monitor module not found."
                " Ensure 'agent_monitor.py' is present to enable agent monitoring."
            )


if __name__ == "__main__":
    main()
