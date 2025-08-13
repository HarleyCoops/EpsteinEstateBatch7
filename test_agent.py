#!/usr/bin/env python3
"""Test the character intelligence agent monitor."""

import yaml
from pathlib import Path
from agent_monitor import start_agent_monitor

def main():
    # Load config
    config_path = Path("config.yaml")
    with open(config_path) as f:
        config = yaml.safe_load(f)
    
    agent_config = config.get("agent", {})
    
    print(f"Starting agent monitor...")
    print(f"- Model: {agent_config.get('model')}")
    print(f"- Watching: {agent_config.get('watch_path')}")
    print(f"- Pattern: {agent_config.get('watch_pattern')}")
    print(f"- Output: {agent_config.get('characters_path')}")
    
    # Start the agent monitor (will run until interrupted)
    start_agent_monitor(agent_config)

if __name__ == "__main__":
    main()