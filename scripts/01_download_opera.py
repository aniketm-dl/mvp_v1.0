#!/usr/bin/env python3
from __future__ import annotations

"""
Step 1: Download OPeRA dataset from Hugging Face.
This is the renamed version of download_opera_dataset.py for sequential pipeline.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.download_opera_dataset import main

if __name__ == "__main__":
    main()
