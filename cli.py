import asyncio
import logging
import os
from typing import List

from ai_tools.speech.speech_to_text import TranscribeFastModel
from ai_tools.speech.text_to_speech import TTSModel

# Optional: prompt_toolkit for autocompletion & suggestions
try:  # pragma: no cover - optional dependency
    from prompt_toolkit import PromptSession
    from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
    from prompt_toolkit.completion import (
        NestedCompleter,
        ThreadedCompleter,
        WordCompleter,
    )
    from prompt_toolkit.history import FileHistory
    from prompt_toolkit.patch_stdout import patch_stdout
    _PTK_AVAILABLE = True
except Exception:
    _PTK_AVAILABLE = False


def setup_logging():
    logging.basicConfig(
        level=os.getenv("LOG_LEVEL", "INFO"),
        format="[%(asctime)s] %(levelname)s %(name)s: %(message)s",
    )
    # Quiet noisy libs unless DEBUG
    quiet = [
        "comtypes.client._code_cache",
        "transformers",
        "httpx",
        "urllib3",
        "jieba._compat",
        "TTS",
    ]
    lvl = logging.DEBUG if os.getenv("LOG_LEVEL", "INFO").upper() == "DEBUG" else logging.WARNING
    for name in quiet:
        logging.getLogger(name).setLevel(lvl)


def _build_completer(existing: List[str]):
    """Create a completer of known commands and verbs."""
    base_cmds = {
        "/quit": None,
        "/q": None,
        ":q": None,
        "exit": None,
        # High-level verbs
        "summarize": {"youtube": None, "web": None, "video": None},
        "music": {"generate": None},
        "web": {"research": None},
        "video": {"summarize": None},
        "stt": {"start": None, "stop": None},
        "tts": {"good": None, "bad": None},
    }
    # Also suggest previously seen phrases as flat words
    words = list({*existing})
    try:
        return NestedCompleter.from_nested_dict(base_cmds)  # type: ignore
    except Exception:
        return WordCompleter(words, ignore_case=True)


async def main():
    setup_logging()
    log = logging.getLogger("cli")

    stt = TranscribeFastModel()
    tts = TTSModel()

    log.info("Voice CLI ready. Press Enter for voice. In recorder, press Ctrl+D to start/stop. Type '/quit' to exit.")

    history_path = os.path.join(os.path.expanduser("~"), ".max_cli_history")
    session = None
    seen: List[str] = []
    completer = None
    if _PTK_AVAILABLE:
        try:
            completer = _build_completer(seen)
            session = PromptSession(
                history=FileHistory(history_path),
                completer=ThreadedCompleter(completer),
            )
        except Exception:
            session = None

    while True:
        try:
            if session is not None:
                # Non-blocking stdout while prompt is active
                with patch_stdout():  # type: ignore
                    cmd = await session.prompt_async(
                        "\nPress Enter to record, or type text to speak (/quit to exit): ",
                        auto_suggest=AutoSuggestFromHistory(),
                        complete_while_typing=True,
                    )
            else:
                cmd = input(
                    "\nPress Enter to record, or type text to speak (/quit to exit): "
                )
            cmd = (cmd or "").strip()
            if cmd:
                seen.append(cmd)
                # Rebuild completer with new words occasionally
                if _PTK_AVAILABLE and session is not None:
                    try:
                        session.completer = ThreadedCompleter(_build_completer(seen))  # type: ignore
                    except Exception:
                        pass

            if cmd.lower() in {"/q", "/quit", ":q", "exit"}:
                print("Bye.")
                return

            if cmd:
                # Simple command routing examples
                low = cmd.lower()
                if low.startswith("tts good"):
                    tts.set_good_model()
                    print("[TTS] Using good model.")
                    continue
                if low.startswith("tts bad"):
                    tts.set_bad_model()
                    print("[TTS] Using pyttsx3.")
                    continue
                # Fall back to speaking the text
                await tts.tts_speak(cmd)
                continue

            # Record and transcribe
            print("Recording... press Enter again to stop.")
            print("Recorder opening... inside it, press Ctrl+D to start/stop recording.")
            text = await stt.run()
            if text:
                print(f"You said: {text}")
                await tts.tts_speak(text)
            else:
                print("(No speech detected)")

        except KeyboardInterrupt:
            print("\nInterrupted. Bye.")
            return
        except EOFError:
            print("\nEOF. Bye.")
            return
        except Exception as e:
            log.exception("CLI error: %s", e)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except RuntimeError:
        # In case of nested event loop (e.g., in some shells), fallback
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main())
