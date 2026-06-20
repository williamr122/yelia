from backend.services.recommendation_service import build_recommendations, recommendations_to_suggestions


def test_build_recommendations_returns_traceable_items(monkeypatch):
    monkeypatch.setattr("backend.services.recommendation_service.has_internet", lambda: False)

    recommendations = build_recommendations(
        user_text="No entiendo clases y objetos, recomiendame recursos",
        topic="Clases y Objetos",
        level="basico",
        emotion={"emotion": "confused", "label": "confusion"},
        intent="explicar",
        history_profile={
            "adaptive": {"weak_topics": ["Clases y Objetos"]},
            "metrics": {"topics": {"Clases y Objetos": 3}},
        },
    )

    assert recommendations
    assert all(item.get("type") for item in recommendations)
    assert all(item.get("title") for item in recommendations)
    assert all(item.get("topic_used") == "Clases y Objetos" for item in recommendations)
    assert all(item.get("level_used") == "basico" for item in recommendations)
    assert any(item.get("history_based") for item in recommendations)
    assert any(item.get("type") == "web_resource" for item in recommendations)

    suggestions = recommendations_to_suggestions(recommendations)
    assert suggestions
    assert all(item.get("label") and item.get("message") for item in suggestions)


def test_recommendations_endpoint_contract(client, monkeypatch):
    from backend.routes import chat_routes_chat

    monkeypatch.setattr(chat_routes_chat, "log_recommendations", lambda **_kwargs: None)
    monkeypatch.setattr("backend.services.recommendation_service.has_internet", lambda: False)

    client.post("/api/auth/login", json={"guest_id": "rec-test"})
    res = client.post(
        "/api/recommendations",
        json={
            "message": "No entiendo herencia, dame recursos web",
            "topic": "Herencia",
            "level": "basico",
            "emotion": {"emotion": "confused", "label": "confusion"},
        },
    )

    assert res.status_code == 200
    data = res.get_json()["data"]
    assert data["contract_version"] == "recommendations.v1"
    assert data["usuario"]
    assert data["topic"] == "Herencia"
    assert data["level"] == "basico"
    assert isinstance(data["recommendations"], list)
    assert data["recommendations"]
    assert isinstance(data["suggestions"], list)
    assert data["evidence"]["table"] == "metrics_recommendations"
    assert data["evidence"]["count"] == len(data["recommendations"])
