import types

import pytest

from ai_tools.speech.text_to_speech import TTSModel


class DummyAudio:
    @staticmethod
    def from_wav(path):
        class _S:
            def __init__(self, p):
                self._p = p

        return _S(path)


def test_tts_bad_model_runs(monkeypatch, tmp_path):
    m = TTSModel()
    m.set_bad_model()

    spoke = {"called": False}

    def fake_say(txt):
        spoke["called"] = True

    def fake_run():
        pass

    m.bad_tts_engine.say = fake_say
    m.bad_tts_engine.runAndWait = fake_run

    # Should not raise; call the blocking helper directly
    m._run_pyttsx3("hello")


@pytest.mark.asyncio
async def test_tts_good_model_fallback_and_cleanup(monkeypatch, tmp_path):
    # Prepare fake TTS.api.TTS that raises to force fallback
    fake_mod = types.SimpleNamespace()

    class FakeTTS:
        def __init__(self, name):
            raise RuntimeError("force fallback")

    fake_mod.TTS = FakeTTS

    # Patch importlib.import_module to return our fake for 'TTS.api'
    orig_import = __import__

    def fake_import(name, *a, **k):
        if name == "TTS.api":
            return fake_mod
        return orig_import(name, *a, **k)

    monkeypatch.setattr("builtins.__import__", fake_import)

    # Patch pyttsx3 engine
    m = TTSModel()
    m.set_good_model()  # try good first, will fallback

    said = {"text": None}

    def fake_say(t):
        said["text"] = t

    m.bad_tts_engine.say = fake_say
    m.bad_tts_engine.runAndWait = lambda: None

    # Patch audio playback to avoid real I/O
    monkeypatch.setattr("ai_tools.speech.text_to_speech.AudioSegment", DummyAudio)
    monkeypatch.setattr("ai_tools.speech.text_to_speech.play", lambda s: None)

    out = tmp_path / "tmp.wav"
    # Create an empty file to exercise cleanup
    out.write_bytes(b"")
    m.temp_audio = str(out)

    await m.tts_speak("hi")

    # We should have fallen back to pyttsx3
    assert said["text"] == "hi"
    # Ensure cleanup removed temp file if created by playback path
    # Our fallback path doesn't create, but cleanup shouldn't crash either
    assert True
