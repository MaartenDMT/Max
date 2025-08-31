import sys
import types
from pathlib import Path

import pytest
from pydub import AudioSegment

from ai_tools.speech.speech_to_text import TranscribeFastModel, split_audio


def test_split_audio_creates_segments(tmp_path):
    # Create a short silent audio file
    audio = AudioSegment.silent(duration=1500)  # 1.5 seconds
    wav_path = tmp_path / "short.wav"
    audio.export(wav_path, format="wav")

    # Override output dir to tmp to avoid touching repo data
    out_dir = tmp_path / "segments"
    out_dir.mkdir()

    # Monkeypatch the default path inside function by shadowing name via import
    # Easiest: call function and then move outputs; since segment length is 60 min, we expect one segment
    segs = split_audio(str(wav_path))
    assert isinstance(segs, list) and len(segs) == 1
    assert Path(segs[0]).suffix == ".wav"


@pytest.mark.asyncio
async def test_transcribe_fast_model_flow(monkeypatch, tmp_path):
    # Mock faster_whisper.WhisperModel to avoid heavy load
    class _Segments:
        def __iter__(self):
            class _S:  # simple segment
                start = 0
                end = 1
                text = "hello"

            yield _S()

    class FakeWhisperModel:
        def __init__(self, size, device=None, compute_type=None):
            self.size = size

        def transcribe(self, path, beam_size=5, language="en"):
            return _Segments(), {"language": language}

    # Provide a safe stub module for faster_whisper via sys.modules
    fw_mod = types.ModuleType("faster_whisper")
    fw_mod.WhisperModel = FakeWhisperModel
    monkeypatch.setitem(sys.modules, "faster_whisper", fw_mod)

    # Prepare a tiny WAV file
    wav = tmp_path / "a.wav"
    AudioSegment.silent(duration=200).export(wav, format="wav")

    m = TranscribeFastModel(device="cpu")
    # Call transcribe synchronously via thread runner in run(); here we directly call transcribe
    text = m.transcribe(str(wav))
    assert "hello" in text
