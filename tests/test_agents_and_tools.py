import json

import pytest

from agents.music_agent import MusicCreationAgent
from agents.video_agent import VideoProcessingAgent
from ai_tools.lc_tools import website_summarize


@pytest.mark.asyncio
async def test_video_agent_input_validation():
    agent = VideoProcessingAgent(transcribe=None)
    res = agent.handle_user_input("")
    assert res["status"] == "error"
    assert "No input" in res["message"]


def test_music_agent_parse_and_validation():
    agent = MusicCreationAgent()
    # Valid
    prompt, bpm, duration = agent.parse_user_input("Generate a 140 BPM hip hop beat for 40 seconds")
    assert bpm == 140 and prompt and duration == 40
    # Missing duration defaults to 30
    prompt3, bpm3, duration3 = agent.parse_user_input("Make a 120 bpm lofi chill beat")
    assert bpm3 == 120 and duration3 == 30 and "lofi" in prompt3
    # Lowercase bpm and punctuation before 'for'
    prompt4, bpm4, duration4 = agent.parse_user_input("Create a 100 bpm drum'n'bass groove, for 25 seconds")
    assert bpm4 == 100 and duration4 == 25 and "groove" in prompt4
    # Singular 'second'
    prompt5, bpm5, duration5 = agent.parse_user_input("Generate a 90 BPM ambient pad for 1 second")
    assert bpm5 == 90 and duration5 == 1 and "ambient" in prompt5
    # Invalid
    prompt2, bpm2, duration2 = agent.parse_user_input("no bpm here")
    assert prompt2 is None and bpm2 is None and duration2 is None

    # Extra text before/after pattern should still parse
    prompt6, bpm6, duration6 = agent.parse_user_input(
        "Hey, please generate a 128 bpm synthwave jam for 45 seconds, thanks!"
    )
    assert bpm6 == 128 and duration6 == 45 and "synthwave" in prompt6

    # Non-integer duration -> default 30
    prompt7, bpm7, duration7 = agent.parse_user_input(
        "Generate a 110 BPM trance lead for thirty seconds"
    )
    assert bpm7 == 110 and duration7 == 30

    # Decimal duration -> default 30
    prompt8, bpm8, duration8 = agent.parse_user_input(
        "Generate a 105 BPM techno loop for 12.5 seconds"
    )
    assert bpm8 == 105 and duration8 == 30


@pytest.mark.asyncio
async def test_website_summarize_tool_handles_error(monkeypatch):
    # Monkeypatch underlying tool to raise
    async def fake_run(url: str, question: str) -> str:
        return json.dumps({"error": "boom"})

    # monkeypatch the _arun of WebsiteSummarizerTool via wrapper: patch the wrapper function directly
    from ai_tools import lc_tools
    original = lc_tools.website_summarize.func
    lc_tools.website_summarize.func = fake_run
    try:
        out = await website_summarize.ainvoke({"url": "https://example.com", "question": "q"})
        data = json.loads(out)
        assert "error" in data
    finally:
        lc_tools.website_summarize.func = original


def test_music_agent_handles_out_of_range_bpm():
    agent = MusicCreationAgent()
    res = agent.handle_user_request("Generate a 10 BPM hip hop beat for 10 seconds")
    assert isinstance(res, dict)
    assert res.get("status") == "error"
    assert "BPM must be an integer between 40 and 240" in res.get("message", "")


def test_music_agent_duration_clamping_and_disabled_generator(monkeypatch):
    agent = MusicCreationAgent()
    # Force generator 'model' to None to simulate missing optional dependency
    agent.loop_generator.model = None

    # Duration below minimum (should clamp to 5), but since generator disabled, we expect an error early
    res1 = agent.handle_user_request("Generate a 140 BPM house loop for 1 second")
    assert res1.get("status") == "error"
    assert "generator is unavailable" in res1.get("message", "").lower()

    # Re-enable generator by faking a model object and intercept generate_loop calls to inspect duration
    class DummyModel:
        pass

    agent.loop_generator.model = DummyModel()

    captured = {}

    def fake_generate_loop(prompt, bpm, duration, output_dir="data/audio/loops/", seed=42):
        captured["prompt"] = prompt
        captured["bpm"] = bpm
        captured["duration"] = duration
        return {"status": "success", "message": "ok", "file_path": "x.wav"}

    monkeypatch.setattr(agent.loop_generator, "generate_loop", fake_generate_loop)

    # Duration above maximum should clamp to 300
    ok = agent.handle_user_request("Generate a 150 BPM techno loop for 9999 seconds")
    assert ok.get("status") == "success"
    assert captured["duration"] == 300
    assert captured["bpm"] == 150
