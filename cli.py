import asyncio
import logging
import os
from typing import List, Dict, Any

from ai_tools.speech.speech_to_text import TranscribeFastModel
from ai_tools.speech.text_to_speech import TTSModel

# Import assistant classes and command functions
from assistents.system_assistent import SystemAssistant
from assistents.ai_assistent import AIAssistant
from utils.call_commands import get_system_commands, get_ai_commands

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
    from prompt_toolkit.key_binding import KeyBindings
    from prompt_toolkit.application import Application
    from prompt_toolkit.buffer import Buffer
    from prompt_toolkit.layout.containers import HSplit, Window
    from prompt_toolkit.layout.controls import BufferControl, FormattedTextControl
    from prompt_toolkit.layout import Layout
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


def _build_completer(existing: List[str], system_commands: Dict[str, Any], ai_commands: Dict[str, Any]):
    """Create a completer of known commands and verbs."""
    # Combine all commands
    all_commands = {}

    # Add system commands
    for cmd in system_commands.keys():
        all_commands[cmd] = None

    # Add AI commands
    for cmd in ai_commands.keys():
        all_commands[cmd] = None

    # Add utility commands
    utility_commands = {
        "/quit": None,
        "/q": None,
        ":q": None,
        "exit": None,
    }
    all_commands.update(utility_commands)

    # Also suggest previously seen phrases as flat words
    words = list({*existing})

    try:
        return NestedCompleter.from_nested_dict(all_commands)  # type: ignore
    except Exception:
        return WordCompleter(words, ignore_case=True)


async def main():
    setup_logging()
    log = logging.getLogger("cli")

    stt = TranscribeFastModel()
    tts = TTSModel()

    # Initialize assistants for command completion
    system_commands = {}
    ai_commands = {}
    try:
        system_assistant = SystemAssistant(tts, None, None)
        ai_assistant = AIAssistant(tts, stt, None, None)

        # Get command dictionaries
        system_commands = get_system_commands(system_assistant)
        ai_commands = get_ai_commands(ai_assistant)
    except Exception:
        log.exception("Failed to initialize assistants for command completion.")
        # Fallback to minimal command set
        system_commands = {
            "time": lambda x: print("Current time command"),
            "joke": lambda x: print("Joke command"),
        }
        ai_commands = {
            "summarize youtube": lambda x: print("YouTube summary command"),
            "research topic": lambda x: print("Research topic command"),
        }

    log.info("Voice CLI ready. Press Enter for voice. In recorder, press Ctrl+D to start/stop. Type '/quit' to exit.")

    history_path = os.path.join(os.path.expanduser("~"), ".max_cli_history")
    session = None
    seen: List[str] = []
    completer = None
    if _PTK_AVAILABLE:
        try:
            completer = _build_completer(seen, system_commands, ai_commands)
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
                        session.completer = ThreadedCompleter(_build_completer(seen, system_commands, ai_commands))  # type: ignore
                    except Exception:
                        pass

            if cmd.lower() in {"/q", "/quit", ":q", "exit"}:
                print("Bye.")
                return

            if cmd:
                # Command routing
                low = cmd.lower()

                # Handle TTS commands
                if low.startswith("tts good"):
                    tts.set_good_model()
                    print("[TTS] Using good model.")
                    continue
                if low.startswith("tts bad"):
                    tts.set_bad_model()
                    print("[TTS] Using pyttsx3.")
                    continue

                # Handle system commands
                command_found = False
                for command, handler in system_commands.items():
                    if low.startswith(command):
                        # For commands that need parameters, we might need to get more input
                        try:
                            if asyncio.iscoroutinefunction(handler):
                                await handler(cmd[len(command):].strip())
                            else:
                                handler(cmd[len(command):].strip())
                            command_found = True
                            break
                        except Exception as e:
                            print(f"[ERROR] Failed to execute system command '{command}': {e}")
                            log.exception("System command error: %s", e)

                # Handle AI commands if no system command matched
                if not command_found:
                    for command, handler in ai_commands.items():
                        if low.startswith(command):
                            try:
                                if asyncio.iscoroutinefunction(handler):
                                    await handler(cmd[len(command):].strip())
                                else:
                                    handler(cmd[len(command):].strip())
                                command_found = True
                                break
                            except Exception as e:
                                print(f"[ERROR] Failed to execute AI command '{command}': {e}")
                                log.exception("AI command error: %s", e)

                # Fall back to speaking the text if no command matched
                if not command_found:
                    # Check if we're in conversation mode
                    if ai_assistant.llm_mode:
                        # Process as conversation input
                        try:
                            result = await ai_assistant._process_conversation_input(cmd)
                            if "error" in result:
                                print(f"[ERROR] {result['error']}")
                            else:
                                print(f"Chatbot: {result['result']}")
                                # Also speak the response
                                await tts.tts_speak(result['result'])
                        except Exception as e:
                            print(f"[ERROR] Failed to process conversation input: {e}")
                            log.exception("Conversation input error: %s", e)
                    else:
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
