#!/usr/bin/env python3
"""
Character intelligence agent monitor.
Watches for translated pages and updates per-character JSON files.
"""

import os
import json
from pathlib import Path

from dotenv import load_dotenv
import openai

try:
    import jsonschema
except ImportError:
    jsonschema = None

from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler


CHARACTER_PROFILE_SCHEMA = {
    "type": "object",
    "properties": {
        "aliases": {"type": "array", "items": {"type": "string"}},
        "dates": {"type": "array", "items": {"type": "string"}},
        "relationships": {"type": "array", "items": {"type": "object"}},
        "events": {"type": "array", "items": {"type": "object"}},
        "locations": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["aliases", "dates", "relationships", "events", "locations"],
    "additionalProperties": True,
}

CHARACTER_SCHEMA = {
    "type": "object",
    "patternProperties": {".*": CHARACTER_PROFILE_SCHEMA},
    "additionalProperties": False,
}


def start_agent_monitor(agent_config: dict) -> None:
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY environment variable not set.")
        return

    openai.api_key = api_key
    watch_path = Path(agent_config.get("watch_path", "english_output"))
    characters_path = Path(agent_config.get("characters_path", "characters"))
    pattern = agent_config.get("watch_pattern", "*_english.txt")

    characters_path.mkdir(parents=True, exist_ok=True)
    processed_file = characters_path / ".processed_files.json"
    if processed_file.exists():
        try:
            processed = set(json.loads(processed_file.read_text(encoding="utf-8")))
        except Exception:
            processed = set()
    else:
        processed = set()


    class NewFileHandler(PatternMatchingEventHandler):
        def __init__(self):
            super().__init__(patterns=[pattern], ignore_directories=True)

        def on_created(self, event):
            self.process(event.src_path)

        def on_modified(self, event):
            self.process(event.src_path)

        def process(self, path_str: str):
            path = Path(path_str)
            if str(path) in processed:
                return
            try:
                text = path.read_text(encoding="utf-8")
                messages = [
                    {"role": "system", "content": agent_config.get("task_instruction")},
                    {"role": "user", "content": text},
                ]
                response = openai.ChatCompletion.create(
                    model=agent_config.get("model"), messages=messages
                )
                content = response.choices[0].message.content
                data = json.loads(content)

                if jsonschema:
                    jsonschema.validate(instance=data, schema=CHARACTER_SCHEMA)
                else:
                    print(
                        "Warning: jsonschema not installed, skipping validation. "
                        "Install with 'pip install jsonschema'."
                    )

                _update_character_files(data, characters_path)
                processed.add(str(path))
                processed_file.write_text(
                    json.dumps(list(processed), indent=2), encoding="utf-8"
                )
                print(f"Processed {path.name}")
            except json.JSONDecodeError as exc:
                print(f"Invalid JSON from agent for {path.name}: {exc}")
            except Exception as exc:
                print(f"Error processing {path.name}: {exc}")


    observer = Observer()
    handler = NewFileHandler()
    observer.schedule(handler, str(watch_path), recursive=False)
    observer.start()
    print(f"Agent monitoring started (model={agent_config.get('model')}). "
          f"Watching '{watch_path}' for '{pattern}'.")

    try:
        observer.join()
    except KeyboardInterrupt:
        observer.stop()
        observer.join()


def _update_character_files(data: dict, characters_path: Path) -> None:
    for name, intel in data.items():
        file_path = characters_path / f"{name}.json"
        if file_path.exists():
            try:
                existing = json.loads(file_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                existing = {}
            merged = {**existing, **intel}
        else:
            merged = intel
        file_path.write_text(json.dumps(merged, indent=2, ensure_ascii=False), encoding="utf-8")
