# OpenAI Codex CLI, GPT‑5, and Current OpenAI API Endpoints (2025 Reference)

Last updated: 2025-08-13

This document consolidates up-to-date details on OpenAI Codex CLI (the local coding agent), the GPT‑5 model family, and the current OpenAI API surfaces and SDK usage you should target in 2025. It is intended as a working reference for development and integration in this repo.

Contents
- Executive summary
- OpenAI Codex CLI (coding agent)
- Models overview (2025) with GPT‑5
- API surfaces to use now: Responses API
- Python SDK (v1.x) examples
- Migration notes from legacy APIs
- Integration patterns and recommendations
- References

## Executive summary

- Codex CLI is a local coding agent you install with npm that can read, write, and run code within your terminal with approval workflows. It defaults to fast reasoning models; you can select models compatible with the Responses API (e.g., o3, GPT‑5 families).
- GPT‑5 is OpenAI’s newest unified system (2025-08-07). It is the default in ChatGPT, with “GPT‑5 thinking” and “GPT‑5 pro” variants for extended reasoning and maximum quality.
- The primary developer API to target is the Responses API. The Python SDK v1.x exposes client.responses.create(...) as the canonical interface. Legacy openai.Completion and raw ChatCompletion usage patterns pre-v1 are deprecated/incompatible without migration.
- The Responses API integrates “tools” including remote MCP servers (changelog: 2025-05-20). This is the correct interface for multi-step agents and tool invocation going forward.

## OpenAI Codex CLI (coding agent)

Codex CLI is an open-source terminal agent that operates locally, supporting multimodal inputs, three approval modes, and model selection.

- Install
  - npm install -g @openai/codex
  - Update: codex --upgrade
- Authenticate
  - Ensure OPENAI_API_KEY is set in your environment
- Start (Suggest mode by default)
  - codex
  - Example prompt: “Explain this repo to me.”
- Approval modes
  - Suggest (default): reads files, proposes changes/commands; requires approval before modifying or executing
  - Auto Edit: can read and write files automatically, but still prompts before shell commands
  - Full Auto: can read, write, and execute commands autonomously inside a sandboxed, network-disabled environment scoped to the current directory
- Mode switches
  - Flags: --suggest, --auto-edit, --full-auto
  - In-session: /mode
- Model selection
  - Defaults to a fast reasoning model (docs reference o4-mini as default)
  - You can specify any model supported by the Responses API (e.g., codex -m gpt-5 or -m o3)
- Windows support
  - Experimental; WSL recommended
- Security note
  - Code reads/writes and local command execution happen locally; only high-level context and prompt content are sent to the model unless you choose to share more

References:
- OpenAI Codex CLI – Getting Started (Help Center)
- GitHub: https://github.com/openai/codex

## Models overview (2025) with GPT‑5

- GPT‑5 (2025-08-07)
  - Unified system routing between a smart model and a deeper “thinking” mode; “GPT‑5 pro” delivers extended reasoning and highest quality
  - Strong gains across coding, math, writing, health, and multimodal; released to ChatGPT with Plus/Pro/Team tiers (different usage limits)
- Developer implications
  - In the API and Codex CLI, you can select GPT‑5 family models via the standard model parameter
  - GPT‑5 is positioned as a direct upgrade path from GPT‑4o/o3 in most use cases

References:
- Introducing GPT‑5 – OpenAI (2025-08-07)
- Introducing GPT‑5 for developers – OpenAI (linked from the blog)

## API surfaces to use now: Responses API

The Responses API is the primary, stateful interface for model interaction in 2025. It unifies capabilities and supersedes legacy patterns in the SDK.

Key points:
- Statefulness: re-use context across turns (e.g., previous_response in the API)
- Tools: integrate file search, web search, code interpreter, and remote MCP servers
- Structured outputs: new flows support text and structured results (community notes reference client.responses.create vs client.responses.parse)

Changelog highlights (2025-05-20):
- Responses API added support for remote MCP servers and code interpreter tools

References:
- API Reference: Responses API – https://platform.openai.com/docs/api-reference/responses
- Changelog – https://platform.openai.com/docs/changelog
- Azure OpenAI Responses API doc corroborates the direction

## Python SDK (v1.x) examples

The official Python SDK (openai on PyPI) uses a new interface since >=1.0.0. The primary method is client.responses.create(...).

Basic text generation:
```python
from openai import OpenAI
client = OpenAI()

response = client.responses.create(
    model="gpt-4.1",  # or "gpt-5" when available to your account
    input="Write a one-sentence bedtime story about a unicorn."
)

print(response.output_text)  # convenience to get aggregated text outputs
```

Notes:
- Legacy openai.Completion or openai.ChatCompletion usage will raise migration errors in v1.x (e.g., “openai.Completion not supported in openai>=1.0.0”).
- For structured output, consult current docs/discussions (community references mention client.responses.parse in addition to create).

JS example (for parity):
```javascript
import { OpenAI } from "openai";
const client = new OpenAI();

const response = await client.responses.create({
  model: "gpt-4.1", // or "gpt-5", as provisioned
  input: "Tell me a three sentence bedtime story about a unicorn."
});

console.log(response.output_text);
```

## Migration notes from legacy APIs

- Legacy: openai.Completion.create(...) and (some) ChatCompletion patterns were common before v1.x. With openai>=1.0.0, these calls are deprecated/incompatible and will raise errors.
- Use client.responses.create(...) as your canonical entry point.
- If your code uses assistants/chats/legacy calls, follow the SDK migration guide or run openai migrate to update your code automatically where supported.

References:
- openai/openai-python – README/api.md (primary API is Responses)
- v1.0.0 Migration Guide – https://github.com/openai/openai-python/discussions/742

## Integration patterns and recommendations

- Codex CLI vs direct API:
  - Use Codex CLI when you want an agent operating locally over your repo with approval modes (suggest/auto-edit/full-auto).
  - Use direct API (Responses) when building programmatic flows, integrating tools (including remote MCP), or needing deterministic, testable interfaces.
- Model choice:
  - Start with GPT‑5 (or gpt‑4.1/o3 where appropriate) based on availability/cost and your use case.
  - Codex CLI defaults to a fast reasoning model; you can override with -m.
- Tooling (MCP/agents):
  - The Responses API supports tool calls and remote MCP servers (per the 2025-05-20 changelog). Prefer building on this for future-proof multi-step agent use.
- Windows workflows:
  - If using Codex CLI on Windows, prefer WSL until Windows support is no longer experimental.

## References

- OpenAI Codex CLI – Getting Started (Help Center):
  - https://help.openai.com/en/articles/11096431-openai-codex-cli-getting-started
- GitHub – OpenAI Codex CLI repo:
  - https://github.com/openai/codex
- OpenAI – Introducing GPT‑5 (2025-08-07):
  - https://openai.com/index/introducing-gpt-5/
- OpenAI – Developer quickstart:
  - https://platform.openai.com/docs/quickstart
- OpenAI – API Reference: Responses API:
  - https://platform.openai.com/docs/api-reference/responses
- OpenAI – API Reference introduction / responses object:
  - https://platform.openai.com/docs/api-reference/introduction
- OpenAI – Docs: Models:
  - https://platform.openai.com/docs/models
- OpenAI – Changelog:
  - https://platform.openai.com/docs/changelog
- OpenAI Python SDK v1 – GitHub:
  - https://github.com/openai/openai-python
- Migration (community + Azure references):
  - https://github.com/openai/openai-python/discussions/742
  - https://learn.microsoft.com/en-us/azure/ai-foundry/openai/how-to/responses
