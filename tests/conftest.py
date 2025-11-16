"""
Pytest configuration and shared fixtures
"""

import pytest
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture(scope="session")
def test_data_dir():
    """Return path to test data directory"""
    return Path(__file__).parent / "test_data"


@pytest.fixture(autouse=True)
def reset_singletons():
    """Reset singleton instances between tests"""
    import backend.services.wellness_coach as wc_module
    import backend.services.graph_rag as gr_module

    wc_module._coach_instance = None
    gr_module._graph_rag_instance = None

    yield

    wc_module._coach_instance = None
    gr_module._graph_rag_instance = None
