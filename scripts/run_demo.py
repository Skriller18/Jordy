from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.data.sample_universe import sample_companies
from app.models import Horizon
from app.scoring.ranking import rank_companies


if __name__ == "__main__":
    response = rank_companies(sample_companies(), horizon=Horizon.LONG_TERM)
    print(json.dumps(response.model_dump(), indent=2))
