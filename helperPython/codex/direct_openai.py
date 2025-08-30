import os
import logging
from typing import Optional

from dotenv import load_dotenv

try:
    from openai import OpenAI  # SDK v1.x
except Exception as e:
    OpenAI = None  # Will be checked at runtime


class CodexDirectAPIWrapper:
    """
    Direct OpenAI API fallback using the modern Responses API (SDK v1.x).
    This avoids legacy Completion/ChatCompletion calls and targets current endpoints.

    Environment:
      - OPENAI_API_KEY must be set (loaded from .env if present)
      - Optional: CODEX_OPENAI_MODEL to override default model

    Notes:
      - Uses client.responses.create(...) and response.output_text for convenience.
      - Passes a 'instructions' system directive to perform German->English Markdown translation.
    """

    def __init__(
        self,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        max_output_tokens: Optional[int] = None,
    ):
        # Load environment variables from .env if present
        load_dotenv()

        # Prefer explicit model override, else env, else a sensible default
        self.model = model or os.getenv("CODEX_OPENAI_MODEL") or "gpt-4.1"
        self.max_output_tokens = max_output_tokens  # None uses server default

        # API key resolution
        api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.api_key = api_key

        if OpenAI is None:
            raise RuntimeError("OpenAI SDK not available. Ensure 'openai' package v1.x is installed.")

        if not self.api_key:
            raise RuntimeError("OPENAI_API_KEY not configured in environment or .env")

        # Initialize client (OpenAI SDK v1.x)
        try:
            self.client = OpenAI(api_key=self.api_key)
        except Exception as e:
            raise RuntimeError(f"Failed to initialize OpenAI client: {e}") from e

        self._logger = logging.getLogger("codex.direct_openai")

    def translate_to_english_markdown(self, german_text: str) -> str:
        """
        Use the Responses API to translate German text into English Markdown.
        """
        if not german_text or not german_text.strip():
            raise ValueError("Empty German text provided to translate")

        instructions = (
            "You are a precise translator. Translate the user's German text into clear English Markdown. "
            "Preserve line breaks and any list-like structure. Do not add commentary beyond the translation."
        )

        kwargs = {
            "model": self.model,
            "input": german_text,
            "instructions": instructions,
        }
        if self.max_output_tokens is not None:
            kwargs["max_output_tokens"] = self.max_output_tokens

        try:
            resp = self.client.responses.create(**kwargs)
            # output_text is a convenience to aggregate output into a plain string
            translation = getattr(resp, "output_text", None)
            if not translation:
                # Fallback: assemble from output blocks if needed
                try:
                    blocks = getattr(resp, "output", []) or []
                    parts = []
                    for b in blocks:
                        if isinstance(b, dict) and b.get("type") == "message":
                            content = b.get("content", [])
                            for c in content:
                                if isinstance(c, dict) and c.get("type") == "output_text":
                                    parts.append(c.get("text", ""))
                    translation = "\n".join(parts).strip()
                except Exception:
                    translation = None

            if not translation:
                raise RuntimeError("No translation text returned from Responses API")

            return translation.strip()

        except Exception as e:
            self._logger.error("Direct OpenAI translation failed: %s", e)
            raise
