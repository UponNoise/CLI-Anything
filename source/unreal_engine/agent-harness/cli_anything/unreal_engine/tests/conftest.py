"""Pytest configuration for Unreal Engine CLI tests."""

import sys
import os
from pathlib import Path

# Add the parent directory to sys.path to allow imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))