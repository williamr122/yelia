def test_chat_response_matches_next_react_contract(client, monkeypatch):
    from backend.routes import chat_routes_chat

    def fake_process(**_kwargs):
        return {
            "respuesta": "Respuesta compatible con Next.",
            "tema": "Programacion Avanzada",
            "modo": "local",
            "web_search": False,
            "modo_interaccion": "normal",
            "intencion": "explicar",
            "profile_used": {"nivel": "basico"},
            "emotion": {
                "emotion": "neutral",
                "label": "neutral",
                "intensity": 0,
                "avatar_expression": "neutral",
            },
        }

    monkeypatch.setattr(chat_routes_chat, "procesar_mensaje_chat", fake_process)
    monkeypatch.setattr(chat_routes_chat, "build_tutor_additions", lambda **_kwargs: {})

    client.post("/api/auth/login", json={"guest_id": "next-chat"})
    res = client.post("/api/chat", json={"message": "Hola YELIA", "conversation_id": None})

    assert res.status_code == 200
    data = res.get_json()["data"]
    assert data["response"] == "Respuesta compatible con Next."
    assert data["reply"] == "Respuesta compatible con Next."
    assert data["answer"] == "Respuesta compatible con Next."
    assert data["conversation_id"]
    assert data["provider"] == "local"
    assert isinstance(data["response_ms"], int)
    assert data["contract_version"] == "chat.v1"
    assert data["web_search"] is False
    assert data["emotion"]["emotion"] == "neutral"
    assert isinstance(data["recommendations"], list)
    assert data["recommendations"]
    assert isinstance(data["suggestions"], list)
    assert data["structured_quiz"] is None
    assert data["structured_grade"] is None
    assert data["avatar"]["version"] == "avatar.v1"
    assert data["diagnostics"]["provider"] == "local"


def test_chat_structured_quiz_contract(client, monkeypatch):
    from backend.routes import chat_routes_chat

    monkeypatch.setattr(chat_routes_chat, "build_tutor_additions", lambda **_kwargs: {})
    client.post("/api/auth/login", json={"guest_id": "next-quiz"})

    res = client.post("/api/chat", json={"message": "Hazme un quiz de clases y objetos"})

    assert res.status_code == 200
    data = res.get_json()["data"]
    assert data["provider"] == "structured"
    assert data["modo_interaccion"] == "quiz"
    assert data["structured_quiz"]["questions"]
    assert data["avatar"]["expression"] == "curious"
