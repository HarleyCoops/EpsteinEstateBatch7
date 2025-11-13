"""Compatibility shim for the relocated Chinese strict pipeline."""
from china_pipeline.pipeline import *  # noqa: F401,F403


if __name__ == "__main__":
    from china_pipeline.pipeline import main

    main()
