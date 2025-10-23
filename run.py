#!/usr/bin/env python3
"""
Main CLI entry point for DeFi Llama Analysis
"""

import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.cli import cli

if __name__ == "__main__":
    cli()
