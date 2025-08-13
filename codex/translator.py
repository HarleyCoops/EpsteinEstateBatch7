import os
import sys
import json
import time
import logging
import subprocess
from typing import List, Tuple, Optional

from .direct_openai import CodexDirectAPIWrapper

"""
Simple translator orchestrator that maps input images to German text files
and translates the German text to English Markdown using a Codex backend.

Two backends are supported:
- Codex via an MCP server (preferred for modularity)
- Codex via a CLI wrapper (fallback)

Directory layout (as used by the repo):
- input/: input images (not read directly here)
- german_output/: German text per image, named <base>_german.txt
- outputs/: English Markdown outputs per image, named <base>.md
"""

logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger("codex.translator")
# Log translations to file as well for auditing
try:
    log_path = os.path.join(os.path.dirname(__file__), "translations.log")
    fh = logging.FileHandler(log_path, encoding="utf-8")
    fh.setLevel(logging.INFO)
    fh.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    LOGGER.addHandler(fh)
except Exception:
    pass

class CodexMCPClient:
    def __init__(self, endpoint: str = "http://localhost:8000"):
        self.endpoint = endpoint.rstrip("/")

    def translate_text(self, source_text: str, format: str = "markdown", mode: str = "german_to_english",
                       retries: int = 3, backoff: float = 0.5) -> str:
        """
        Call the Codex MCP endpoint to translate text.

        Endpoint expected (example):
          POST {endpoint}/translate
          {
            "source_text": "...",
            "format": "markdown",
            "mode": "german_to_english"
          }
        Response:
          {"translation": "..."}
        """
        try:
            import requests  # Local import to avoid hard dependency at import time
        except Exception as e:
            raise RuntimeError("requests library is required for Codex MCP integration") from e

        payload = {
            "source_text": source_text,
            "format": format,
            "mode": mode
        }

        url = f"{self.endpoint}/translate"
        for attempt in range(1, retries + 1):
            try:
                resp = requests.post(url, json=payload, timeout=15)
                resp.raise_for_status()
                data = resp.json()
                translation = data.get("translation")
                if translation is None:
                    raise ValueError("No translation returned in MCP response")
                return translation
            except Exception as exc:
                if attempt == retries:
                    raise
                wait = backoff * (2 ** (attempt - 1))
                LOGGER.warning("Codex MCP translation failed (attempt %d/%d). Retrying in %.1fs...",
                               attempt, retries, wait)
                time.sleep(wait)
        raise RuntimeError("Unreachable: MCP translation failed after retries")

class CodexCLIWrapper:
    def __init__(self, cli_cmd: str = "codex"):
        self.cli_cmd = cli_cmd

    def translate_text(self, source_text: str, timeout: int = 60) -> str:
        """
        Translate German text to English Markdown using a Codex CLI wrapper.

        Assumes a CLI command exists like:
          codex-cli translate --text "<text>" --format markdown --mode german_to_english
        Returns the translation as a string.
        """
        # NOTE: This is a best-effort wrapper. If the CLI isn't present, it will raise.
        cmd = [
            self.cli_cmd,
            "translate",
            "--text",
            source_text,
            "--format",
            "markdown",
            "--mode",
            "german_to_english"
        ]
        try:
            import shlex
            import subprocess
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        except Exception as e:
            raise RuntimeError(f"Failed to run Codex CLI wrapper: {e}") from e

        if proc.returncode != 0:
            err = proc.stderr.strip() or proc.stdout.strip()
            raise RuntimeError(f"Codex CLI wrapper failed: {err}")
        return proc.stdout.strip()

def discover_pairs(input_dir: str, german_dir: str) -> List[Tuple[str, str, str]]:
    """
    Discover pairs of (input_image_path, german_text_path, base_name)
    based on the naming convention:
      input: .../<base>.*.jpeg/.jpg/.png
      german_text: german_output/<base>_german.txt
    Returns a list of tuples (input_path, german_path, base_name).
    """
    pairs: List[Tuple[str, str, str]] = []
    if not os.path.isdir(input_dir):
        LOGGER.error("Input directory not found: %s", input_dir)
        return pairs
    if not os.path.isdir(german_dir):
        LOGGER.error("German text directory not found: %s", german_dir)
        return pairs

    for root, _, files in os.walk(input_dir):
        for f in files:
            if not f.lower().endswith((".jpeg", ".jpg", ".png", ".tiff", ".bmp", ".gif")):
                continue
            input_path = os.path.join(root, f)
            base = os.path.splitext(os.path.basename(f))[0]
            german_path = os.path.join(german_dir, f"{base}_german.txt")
            if os.path.exists(german_path):
                pairs.append((input_path, german_path, base))
            else:
                LOGGER.debug("No German text found for input %s (expected %s)", input_path, german_path)
    return pairs

def read_german_text(german_path: str) -> str:
    with open(german_path, "r", encoding="utf-8") as f:
        return f.read().strip()

def ensure_dir(path: str):
    if not os.path.isdir(path):
        os.makedirs(path, exist_ok=True)

def write_output(output_dir: str, base: str, content: str):
    ensure_dir(output_dir)
    out_path = os.path.join(output_dir, f"{base}.md")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(content)
    LOGGER.info("Wrote EnglishMarkdown: %s", out_path)

def process_all(input_dir: str,
                german_dir: str,
                output_dir: str,
                use_mcp: bool = True,
                mcp_endpoint: str = "http://localhost:8000",
                cli_cmd: str = "codex",
                dry_run: bool = False,
                limit: Optional[int] = None,
                verbose: bool = False) -> None:
    """
    Orchestrate the end-to-end process:
    - Discover pairs
    - Translate German text to English Markdown via MCP or CLI wrapper
    - Write outputs (unless dry_run)
    """
    if verbose:
        LOGGER.setLevel(logging.DEBUG)

    pairs = discover_pairs(input_dir, german_dir)
    if limit is not None:
        pairs = pairs[:max(0, limit)]
    if not pairs:
        LOGGER.warning("No input/german pairs found. Nothing to translate.")
        return

    LOGGER.info("Found %d input/german pairs to translate.", len(pairs))

    if use_mcp:
        mcp_client = CodexMCPClient(endpoint=mcp_endpoint)
    else:
        mcp_client = None
    cli_wrapper = CodexCLIWrapper(cli_cmd=cli_cmd)

    translated = 0
    skipped = 0

    for idx, (input_path, german_path, base) in enumerate(pairs, start=1):
        if dry_run:
            LOGGER.info("[DRY-RUN] Processing %s -> %s", input_path, base)
            translated += 1
            continue

        try:
            german_text = read_german_text(german_path)
            if use_mcp and mcp_client is not None:
                translation = mcp_client.translate_text(
                    source_text=german_text,
                    mode="german_to_english",
                    format="markdown"
                )
            else:
                translation = cli_wrapper.translate_text(
                    source_text=german_text
                )
            write_output(output_dir, base, translation)
            translated += 1
        except Exception as exc:
            LOGGER.error("Failed to translate %s: %s", input_path, exc)
            translation = None
            try:
                if 'german_text' in locals() and german_text:
                    wrapper = CodexDirectAPIWrapper()
                    translation = wrapper.translate_to_english_markdown(german_text)
            except Exception as _e:
                LOGGER.error("Direct Codex fallback failed for %s: %s", input_path, _e)
                translation = None
            if translation is not None:
                write_output(output_dir, base, translation)
                translated += 1
                continue
            skipped += 1
            continue

    LOGGER.info("Translation complete. Translated: %d; Skipped: %d", translated, skipped)

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Codex-based German→English translator for DorleStories.")
    parser.add_argument("--input-dir", default="input", help="Directory containing input images")
    parser.add_argument("--german-dir", default="german_output", help="Directory containing German text outputs")
    parser.add_argument("--output-dir", default="codex/outputs", help="Directory to write English Markdown outputs")
    parser.add_argument("--use-mcp", action="store_true", help="Use Codex MCP backend (default: True)")
    parser.add_argument("--mcp-endpoint", default="http://localhost:8000",
                        help="Codex MCP HTTP endpoint (if --use-mcp is set)")
    parser.add_argument("--cli-cmd", default="codex", help="Codex CLI command wrapper (fallback)")
    parser.add_argument("--dry-run", action="store_true", help="Preview actions without writing files")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of pairs to process")
    parser.add_argument("--verbose", action="store_true", help="Verbose logging")

    args = parser.parse_args()

    process_all(
        input_dir=args.input_dir,
        german_dir=args.german_dir,
        output_dir=args.output_dir,
        use_mcp=args.use_mcp,
        mcp_endpoint=args.mcp_endpoint,
        cli_cmd=args.cli_cmd,
        dry_run=args.dry_run,
        limit=args.limit,
        verbose=args.verbose
    )
