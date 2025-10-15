#!/usr/bin/env python3
"""Wrapper script to run OPeRA parser with correct imports."""
from __future__ import annotations

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.data.opera.parse_opera import main

if __name__ == "__main__":
    main()
