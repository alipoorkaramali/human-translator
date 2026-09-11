# =============================================================================
# src/processor.py - (legacy / unused - main uses src.core.pipeline)
# Kept for compatibility; prefer src.core.pipeline.Pipeline
# =============================================================================
from typing import Optional

import pandas as pd

from src.ht_token import Token
from src.utils import (
    preprocess_text, tokenize_english,
    number_type, is_possessive_or_s,
)
