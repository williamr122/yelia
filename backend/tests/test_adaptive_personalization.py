from backend.services.adaptive_content_service import build_adaptive_plan


def test_build_adaptive_plan_reinforces_weak_topic():
    plan = build_adaptive_plan(
        profile={
            "level_current": "intermedio",
            "adaptive": {
                "learning_state": "needs_reinforcement",
                "weak_topics": ["Herencia"],
                "mastered_topics": [],
            },
        },
        topic="Herencia",
        requested_level="intermedio",
        emotion={"emotion": "confused", "label": "confusion"},
        intent="explicar",
        personalized_feedback={"status": "needs_help", "kind": "needs_reinforcement"},
    )

    assert plan["contract_version"] == "adaptive_personalization.v1"
    assert plan["topic"] == "Herencia"
    assert plan["current_level"] == "intermedio"
    assert plan["selected_level"] == "basico"
    assert plan["should_change_level"] is True
    assert plan["strategy"] == "reinforce_foundations"
    assert plan["next_best_action"] == "explain_simpler"
    assert plan["content_adjustments"]["pace"] == "slow"


def test_build_adaptive_plan_increases_challenge_for_mastered_topic():
    plan = build_adaptive_plan(
        profile={
            "level_current": "intermedio",
            "adaptive": {
                "learning_state": "progressing",
                "weak_topics": [],
                "mastered_topics": ["Polimorfismo"],
            },
        },
        topic="Polimorfismo",
        requested_level="intermedio",
        emotion={"emotion": "satisfied"},
        intent="explicar",
        personalized_feedback={"status": "progress", "kind": "understood"},
    )

    assert plan["selected_level"] == "avanzado"
    assert plan["strategy"] == "increase_challenge"
    assert plan["next_best_action"] == "practice_or_quiz"


def test_adaptive_plan_endpoint_contract(client, monkeypatch):
    from backend.routes import chat_routes_chat

    monkeypatch.setattr(
        chat_routes_chat,
        "get_profile",
        lambda _usuario: {
            "level_current": "intermedio",
            "adaptive": {
                "learning_state": "needs_reinforcement",
                "weak_topics": ["Clases y Objetos"],
                "mastered_topics": [],
            },
        },
    )
    monkeypatch.setattr(chat_routes_chat, "save_adaptive_plan", lambda *_args, **_kwargs: None)

    client.post("/api/auth/login", json={"guest_id": "adaptive-plan-test"})
    res = client.post(
        "/api/adaptive-plan",
        json={
            "message": "No entiendo clases y objetos",
            "topic": "Clases y Objetos",
            "level": "intermedio",
            "emotion": {"emotion": "confused"},
            "personalized_feedback": {"status": "needs_help", "kind": "needs_reinforcement"},
        },
    )

    assert res.status_code == 200
    data = res.get_json()["data"]
    plan = data["adaptive_plan"]

    assert data["contract_version"] == "adaptive_personalization.v1"
    assert plan["contract_version"] == "adaptive_personalization.v1"
    assert plan["selected_level"] == "basico"
    assert plan["strategy"] == "reinforce_foundations"
    assert data["evidence"]["profile_source"] == "student_profiles.profile_json"
