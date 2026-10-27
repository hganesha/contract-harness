#!/usr/bin/env python3
"""Convenience entry point: python run.py --config harness.config.json"""
from harness.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
