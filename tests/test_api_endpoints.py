from fastapi.testclient import TestClient

from api.main_api import app
from api.routers import ai_router, system_router
from api.schemas import ChatbotRequest, SystemCommandRequest


class _StubAIAssistant:
    async def _handle_chatbot_api(self, mode: str, summary: str, full_text: str):
        return {"result": f"mode={mode}; len={len(full_text)}"}


class _StubSystemAssistant:
    async def _handle_command_api(self, command: str):
        return {"status": "success", "message": f"executed: {command}", "data": {}}


def _override_ai_dep():
    async def _get():
        return _StubAIAssistant()

    return _get


def _override_system_dep():
    async def _get():
        return _StubSystemAssistant()

    return _get


def test_root_ok():
    client = TestClient(app)
    r = client.get("/")
    assert r.status_code == 200
    assert "message" in r.json()


def test_system_health_ok():
    client = TestClient(app)
    r = client.get("/system/health")
    assert r.status_code == 200
    body = r.json()
    assert body.get("status") == "ok"
    assert "features" in body


def test_chatbot_endpoint_with_override(monkeypatch):
    # Override dependency to avoid loading heavy models
    app.dependency_overrides[ai_router.get_ai_assistant] = _override_ai_dep()
    try:
        client = TestClient(app)
        req = ChatbotRequest(mode="critique", summary="s", full_text="hello world")
        r = client.post("/ai/chatbot", json=req.model_dump())
        assert r.status_code == 200
        assert "result" in r.json()
    finally:
        app.dependency_overrides.pop(ai_router.get_ai_assistant, None)


def test_system_command_with_override(monkeypatch):
    app.dependency_overrides[system_router.get_system_assistant] = _override_system_dep()
    try:
        client = TestClient(app)
        req = SystemCommandRequest(command="noop")
        r = client.post("/system/command", json=req.model_dump())
        assert r.status_code == 200
        body = r.json()
        assert body.get("status") == "success"
        assert "executed" in body.get("message", "")
    finally:
        app.dependency_overrides.pop(system_router.get_system_assistant, None)
