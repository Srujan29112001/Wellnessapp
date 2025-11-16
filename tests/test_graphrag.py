"""
Tests for GraphRAG Service
"""

import pytest
from backend.services.graph_rag import GraphRAG


@pytest.fixture
def graph_rag():
    """Create GraphRAG instance"""
    return GraphRAG()


def test_find_treatments_for_symptoms(graph_rag):
    """Test finding treatments for symptoms"""
    symptoms = ["High Stress", "Poor Sleep"]

    treatments = graph_rag.find_treatments_for_symptoms(symptoms, limit=5)

    assert isinstance(treatments, list)
    assert len(treatments) <= 5

    if treatments:
        treatment = treatments[0]
        assert "name" in treatment
        assert "type" in treatment
        # assert "efficacy" in treatment


def test_find_dosha_balancing_recommendations(graph_rag):
    """Test dosha recommendations"""
    dosha = "Vata"

    recommendations = graph_rag.find_dosha_balancing_recommendations(dosha)

    assert "dosha" in recommendations
    assert recommendations["dosha"] == dosha
    assert "balancing_foods" in recommendations
    assert "recommended_herbs" in recommendations


def test_complex_reasoning_query(graph_rag):
    """Test complex reasoning"""
    user_state = {
        "symptoms": ["High Stress"],
        "current_supplements": [],
        "dosha": "Pitta",
        "contraindications": []
    }

    result = graph_rag.complex_reasoning_query(user_state)

    assert "new_supplements" in result
    assert "practices" in result
    assert "dietary_changes" in result
    assert "warnings" in result


def test_fallback_mode(graph_rag):
    """Test that fallback mode works when Neo4j is unavailable"""
    # Even without Neo4j connection, should return results
    symptoms = ["High Stress"]
    treatments = graph_rag._fallback_find_treatments(symptoms)

    assert isinstance(treatments, list)
    assert len(treatments) > 0
