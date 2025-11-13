"""Compatibility shim delegating to china_pipeline.image_translator."""
from china_pipeline.image_translator import *  # noqa: F401,F403


if __name__ == "__main__":
    from china_pipeline.image_translator import main

    main()
