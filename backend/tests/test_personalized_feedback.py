from backend.services.personalized_feedback_service import build_personalized_feedback


def test_build_personalized_feedback_returns_traceable_contract():
    feedback = build_personalized_feedback(
        user_text="No entiendo herencia, explicame mas simple",
        topic="Herencia",
        level="basico",
        emotion={"emotion": "confused", "label": "confusion"},
        intent="explicar",
        mode="normal",
    )

    assert feedback
    assert feedback["contract_version"] == "personalized_feedback.v1"
    assert feedback["detected"] is True
    assert feedback["kind"] == "needs_reinforcement"
    assert feedback["status"] == "needs_help"
    assert feedback["topic"] == "Herencia"
    assert feedback["level"] == "basico"
    assert feedback["summary"]
    assert feedback["action"]
    assert feedback["reason"]
    assert "needs_reinforcement" in feedback["evidence_tags"]


def test_personalized_feedback_endpoint_updates_profile_and_logs(client, monkeypatch):
    from backend.routes import chat_routes_chat

    logged = {"called": False}

    def fake_log_adaptive_feedback(**_kwargs):
        logged["called"] = True

    def fake_update_adaptive_profile(**_kwargs):
        return {
            "adaptive_summary": {
                "learning_state": "needs_reinforcement",
                "next_best_action": "explain_simpler",
            }
        }

    monkeypatch.setattr(chat_routes_chat, "log_adaptive_feedback", fake_log_adaptive_feedback)
    monkeypatch.setattr(chat_routes_chat, "update_adaptive_profile", fake_update_adaptive_profile)

    client.post("/api/auth/login", json={"guest_id": "feedback-test"})
    res = client.post(
        "/api/personalized-feedback",
        json={
            "message": "No entiendo polimorfismo, me confunde",
            "topic": "Polimorfismo",
            "level": "basico",
            "emotion": {"emotion": "confused", "label": "confusion"},
            "conversation_id": 7,
        },
    )

    assert res.status_code == 200
    data = res.get_json()["data"]
    feedback = data["personalized_feedback"]

    assert data["contract_version"] == "personalized_feedback.v1"
    assert data["conversation_id"] == 7
    assert feedback["detected"] is True
    assert feedback["summary"]
    assert feedback["action"]
    assert data["adaptive_profile"]["learning_state"] == "needs_reinforcement"
    assert data["evidence"]["table"] == "metrics_adaptive_feedback"
    assert data["evidence"]["detected"] is True
    assert logged["called"] is True


def test_personalized_feedback_endpoint_no_signal_is_non_destructive(client, monkeypatch):
    from backend.routes import chat_routes_chat

    logged = {"called": False}

    monkeypatch.setattr(
        chat_routes_chat,
        "log_adaptive_feedback",
        lambda **_kwargs: logged.update(called=True),
    )
    monkeypatch.setattr(chat_routes_chat, "update_adaptive_profile", lambda **_kwargs: None)

    client.post("/api/auth/login", json={"guest_id": "feedback-no-signal"})
    res = client.post(
        "/api/personalized-feedback",
        json={
            "message": "Hola YELIA",
            "topic": "Programacion Avanzada",
            "level": "intermedio",
        },
    )

    assert res.status_code == 200
    data = res.get_json()["data"]
    feedback = data["personalized_feedback"]

    assert feedback["contract_version"] == "personalized_feedback.v1"
    assert feedback["detected"] is False
    assert feedback["kind"] == "no_signal"
    assert data["evidence"]["logged"] is False
    assert logged["called"] is False
