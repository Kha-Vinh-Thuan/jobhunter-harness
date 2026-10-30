#!/usr/bin/env python3
"""Entry point for the development harness; it contains no application runtime."""

from harnesslib.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
