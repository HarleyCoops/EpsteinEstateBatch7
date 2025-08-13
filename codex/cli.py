import argparse
from .translator import process_all

def main():
    parser = argparse.ArgumentParser(description="Codex-backed translator for German-to-English in DorleStories.")
    parser.add_argument("--input-dir", default="input", help="Directory containing input images")
    parser.add_argument("--german-dir", default="german_output", help="Directory containing German text outputs")
    parser.add_argument("--output-dir", default="codex/outputs", help="Directory to write English Markdown outputs")
    parser.add_argument("--use-mcp", action="store_true", help="Use Codex MCP backend (default path).")
    parser.add_argument("--mcp-endpoint", default="http://localhost:8000", help="Codex MCP HTTP endpoint.")
    parser.add_argument("--cli-cmd", default="codex-cli", help="Codex CLI command wrapper (fallback).")
    parser.add_argument("--dry-run", action="store_true", help="Preview actions without writing files.")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of pairs to process.")
    parser.add_argument("--verbose", action="store_true", help="Verbose logging.")

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

if __name__ == "__main__":
    main()
