"""Shared test fixtures and configuration."""
import sys
from pathlib import Path

# Ensure project root is on sys.path
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
