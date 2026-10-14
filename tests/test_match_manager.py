"""Manual slide matches must keep living in <repo>/data/manual_matches.json after the move to pbp/core."""

import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)

from pbp.core.match_manager import MANUAL_MATCHES_FILE  # noqa: E402


def test_manual_matches_file_is_in_repo_data_folder():
    assert MANUAL_MATCHES_FILE == os.path.join(REPO_ROOT, "data", "manual_matches.json")
