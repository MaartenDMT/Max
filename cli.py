import asyncio
import logging
import os
import signal
import sys
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
        FuzzyCompleter,
        PathCompleter,
    )
    from prompt_toolkit.history import FileHistory
    from prompt_toolkit.patch_stdout import patch_stdout
    from prompt_toolkit.key_binding import KeyBindings
    from prompt_toolkit.application import Application
    from prompt_toolkit.buffer import Buffer
    from prompt_toolkit.layout.containers import HSplit, Window
    from prompt_toolkit.layout.controls import BufferControl, FormattedTextControl
    from prompt_toolkit.layout import Layout
    from prompt_toolkit.styles import Style
    from prompt_toolkit.formatted_text import HTML, to_formatted_text
    from prompt_toolkit.shortcuts import ProgressBar
    from prompt_toolkit.filters import Condition
    from prompt_toolkit.keys import Keys
    from prompt_toolkit.output.win32 import NoConsoleScreenBufferError
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


# Custom style for the CLI
custom_style = Style.from_dict({
    'prompt': '#ansigreen bold',
    'recording': '#ansiyellow bold',
    'output': '#ansiblue',
    'error': '#ansired bold',
    'info': '#ansicyan',
})


# Global variables to store references to assistants for cleanup
system_assistant = None
ai_assistant = None


def signal_handler(sig, frame):
    """Handle shutdown signals gracefully."""
    log = logging.getLogger("cli")
    log.info("Received signal %s, shutting down gracefully...", sig)
    
    # Clean up resources
    global system_assistant, ai_assistant
    if system_assistant:
        system_assistant.cleanup()
    if ai_assistant:
        ai_assistant.cleanup()
    
    print("\nReceived interrupt signal. Bye.")
    sys.exit(0)


def _build_completer(existing: List[str], system_commands: Dict[str, Any], ai_commands: Dict[str, Any]):
    """Create a completer of known commands and verbs."""
    # Combine all commands
    all_commands = {}

    # Add system commands with descriptions
    for cmd in system_commands.keys():
        all_commands[cmd] = None

    # Add AI commands with descriptions
    for cmd in ai_commands.keys():
        all_commands[cmd] = None

    # Add utility commands
    utility_commands = {
        "/quit": None,
        "/q": None,
        ":q": None,
        "exit": None,
        "help": None,
        "clear": None,
        "history": None,
    }
    all_commands.update(utility_commands)

    # Add file path completion for file-related commands
    file_commands = {
        "open file": PathCompleter(expanduser=True),
        "delete file": PathCompleter(expanduser=True),
        "create folder": PathCompleter(expanduser=True),
    }
    
    # Combine commands with nested structure
    nested_commands = {}
    for cmd, completer in all_commands.items():
        if cmd in file_commands:
            nested_commands[cmd] = file_commands[cmd]
        else:
            nested_commands[cmd] = completer

    # Also suggest previously seen phrases as flat words
    words = list({*existing})

    try:
        # Use FuzzyCompleter for better matching
        nested_completer = NestedCompleter.from_nested_dict(nested_commands)
        return FuzzyCompleter(nested_completer)
    except Exception:
        return WordCompleter(words, ignore_case=True)


def _get_command_descriptions():
    """Get descriptions for commands to show in help."""
    return {
        "time": "Get current time",
        "open edge": "Open Microsoft Edge browser",
        "what is your name": "Get assistant's name",
        "who are you": "Get assistant's name",
        "play": "Play a song on YouTube",
        "joke": "Tell a random joke",
        "minimize": "Minimize active window",
        "maximize": "Maximize active window",
        "close": "Close active window",
        "volume up": "Increase system volume",
        "volume down": "Decrease system volume",
        "mute": "Mute system volume",
        "shutdown system": "Shutdown the system",
        "restart system": "Restart the system",
        "lock screen": "Lock the screen",
        "sleep system": "Put system to sleep",
        "open app": "Open an application",
        "open file": "Open a file",
        "delete file": "Delete a file",
        "create folder": "Create a folder",
        "move file": "Move a file to a folder",
        "battery status": "Get battery status",
        "cpu usage": "Get CPU usage",
        "memory usage": "Get memory usage",
        "disk space": "Get disk space information",
        "weather": "Get weather information",
        "set alarm": "Set an alarm",
        "take screenshot": "Take a screenshot",
        "calculate": "Perform a calculation",
        "summarize youtube": "Summarize a YouTube video",
        "summarize website": "Summarize a website",
        "music loop": "Generate a music loop",
        "research topic": "Research a topic",
        "critique text": "Set critique mode",
        "reflect on text": "Set reflecting mode",
        "casual chat": "Set casual chat mode",
        "professional chat": "Set professional chat mode",
        "creative brainstorm": "Set creative mode",
        "analytical analysis": "Set analytical mode",
        "chat with": "Start conversation with chatbot",
        "exit chat": "Exit conversation mode",
        "write book": "Write a book",
        "write story": "Write a story",
        "create story": "Create a story",
        "/quit": "Exit the application",
        "help": "Show this help message",
        "clear": "Clear the screen",
        "history": "Show command history",
    }


async def _show_help(session):
    """Display help information."""
    descriptions = _get_command_descriptions()
    
    if session:
        session.output.write("\n")
        session.output.write(to_formatted_text(HTML("<b>Available Commands:</b>\n")))
        session.output.write("=" * 50 + "\n")
        
        # Group commands by type
        system_cmds = [cmd for cmd in descriptions.keys() if cmd.startswith(("time", "open", "play", "joke", "volume", "shutdown", "restart", "lock", "sleep", "battery", "cpu", "memory", "disk", "weather", "take", "calculate"))]
        ai_cmds = [cmd for cmd in descriptions.keys() if cmd.startswith(("summarize", "music", "research", "critique", "reflect", "casual", "professional", "creative", "analytical", "chat", "write"))]
        utility_cmds = [cmd for cmd in descriptions.keys() if cmd.startswith(("/", ":", "exit", "help", "clear", "history"))]
        
        if system_cmds:
            session.output.write(to_formatted_text(HTML("<b>System Commands:</b>\n")))
            for cmd in system_cmds:
                session.output.write(f"  {cmd:<25} - {descriptions.get(cmd, 'No description')}\n")
            session.output.write("\n")
            
        if ai_cmds:
            session.output.write(to_formatted_text(HTML("<b>AI Commands:</b>\n")))
            for cmd in ai_cmds:
                session.output.write(f"  {cmd:<25} - {descriptions.get(cmd, 'No description')}\n")
            session.output.write("\n")
            
        if utility_cmds:
            session.output.write(to_formatted_text(HTML("<b>Utility Commands:</b>\n")))
            for cmd in utility_cmds:
                session.output.write(f"  {cmd:<25} - {descriptions.get(cmd, 'No description')}\n")
            session.output.write("\n")
            
        session.output.flush()
    else:
        print("\nAvailable Commands:")
        print("=" * 50)
        for cmd, desc in descriptions.items():
            print(f"  {cmd:<25} - {desc}")


async def main():
    setup_logging()
    log = logging.getLogger("cli")

    stt = TranscribeFastModel()
    tts = TTSModel()

    # Initialize assistants for command completion
    global system_assistant, ai_assistant
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

    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    log.info("Voice CLI ready. Press Enter for voice. In recorder, press Ctrl+D to start/stop. Type '/quit' to exit.")

    history_path = os.path.join(os.path.expanduser("~"), ".max_cli_history")
    session = None
    seen: List[str] = []
    completer = None
    
    # Create key bindings
    kb = KeyBindings() if _PTK_AVAILABLE else None
    
    if kb:
        @kb.add('c-l')
        def _(event):
            """Clear the screen."""
            if session:
                session.output.write("\x1b[2J\x1b[H")
                session.output.flush()
    
    if _PTK_AVAILABLE:
        try:
            completer = _build_completer(seen, system_commands, ai_commands)
            session = PromptSession(
                history=FileHistory(history_path),
                completer=ThreadedCompleter(completer),
                auto_suggest=AutoSuggestFromHistory(),
                style=custom_style,
                key_bindings=kb,
            )
        except NoConsoleScreenBufferError:
            log.warning("Failed to initialize prompt toolkit due to console incompatibility. Using basic input mode.")
            session = None
        except Exception as e:
            log.exception("Failed to initialize prompt toolkit: %s", e)
            session = None

    while True:
        try:
            if session is not None:
                # Non-blocking stdout while prompt is active
                with patch_stdout():  # type: ignore
                    cmd = await session.prompt_async(
                        HTML("<prompt>Max Assistant</prompt> &gt; "),
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
                if session:
                    session.output.write("Bye.\n")
                else:
                    print("Bye.")
                return

            if cmd:
                # Command routing
                low = cmd.lower()

                # Handle utility commands
                if low in {"help", "h"}:
                    await _show_help(session)
                    continue
                elif low == "clear":
                    if session:
                        session.output.write("\x1b[2J\x1b[H")
                        session.output.flush()
                    else:
                        os.system('cls' if os.name == 'nt' else 'clear')
                    continue
                elif low == "history":
                    if session:
                        history = session.history.get_strings()
                        session.output.write("\nCommand History:\n")
                        session.output.write("=" * 20 + "\n")
                        for i, item in enumerate(history[-10:], 1):
                            session.output.write(f"{i:2d}. {item}\n")
                        session.output.write("\n")
                        session.output.flush()
                    else:
                        print("History not available in basic mode")
                    continue

                # Handle TTS commands
                if low.startswith("tts good"):
                    tts.set_good_model()
                    if session:
                        session.output.write(to_formatted_text(HTML("<info>[TTS] Using good model.</info>\n")))
                    else:
                        print("[TTS] Using good model.")
                    continue
                if low.startswith("tts bad"):
                    tts.set_bad_model()
                    if session:
                        session.output.write(to_formatted_text(HTML("<info>[TTS] Using pyttsx3.</info>\n")))
                    else:
                        print("[TTS] Using pyttsx3.")
                    continue

                # Handle system commands
                command_found = False
                for command, handler in system_commands.items():
                    if low.startswith(command):
                        # For commands that need parameters, we might need to get more input
                        try:
                            if asyncio.iscoroutinefunction(handler):
                                result = await handler(cmd[len(command):].strip())
                            else:
                                result = handler(cmd[len(command):].strip())
                            
                            if session:
                                if isinstance(result, dict) and "message" in result:
                                    session.output.write(to_formatted_text(HTML(f"<output>{result['message']}</output>\n")))
                                elif result:
                                    session.output.write(to_formatted_text(HTML(f"<output>{result}</output>\n")))
                            command_found = True
                            break
                        except Exception as e:
                            error_msg = f"[ERROR] Failed to execute system command '{command}': {e}"
                            if session:
                                session.output.write(to_formatted_text(HTML(f"<error>{error_msg}</error>\n")))
                            else:
                                print(error_msg)
                            log.exception("System command error: %s", e)

                # Handle AI commands if no system command matched
                if not command_found:
                    for command, handler in ai_commands.items():
                        if low.startswith(command):
                            try:
                                # Show processing indicator
                                if session:
                                    session.output.write(to_formatted_text(HTML("<info>Processing...</info>\n")))
                                
                                if asyncio.iscoroutinefunction(handler):
                                    result = await handler(cmd[len(command):].strip())
                                else:
                                    result = handler(cmd[len(command):].strip())
                                
                                if session:
                                    if isinstance(result, dict):
                                        if "error" in result:
                                            session.output.write(to_formatted_text(HTML(f"<error>[ERROR] {result['error']}</error>\n")))
                                        elif "message" in result:
                                            session.output.write(to_formatted_text(HTML(f"<output>{result['message']}</output>\n")))
                                        elif "result" in result:
                                            session.output.write(to_formatted_text(HTML(f"<output>{result['result']}</output>\n")))
                                    elif result:
                                        session.output.write(to_formatted_text(HTML(f"<output>{result}</output>\n")))
                                command_found = True
                                break
                            except Exception as e:
                                error_msg = f"[ERROR] Failed to execute AI command '{command}': {e}"
                                if session:
                                    session.output.write(to_formatted_text(HTML(f"<error>{error_msg}</error>\n")))
                                else:
                                    print(error_msg)
                                log.exception("AI command error: %s", e)

                # Fall back to speaking the text if no command matched
                if not command_found:
                    # Check if we're in conversation mode
                    if ai_assistant.llm_mode:
                        # Process as conversation input
                        try:
                            if session:
                                session.output.write(to_formatted_text(HTML("<info>Processing conversation...</info>\n")))
                            
                            result = await ai_assistant._process_conversation_input(cmd)
                            if "error" in result:
                                error_msg = f"[ERROR] {result['error']}"
                                if session:
                                    session.output.write(to_formatted_text(HTML(f"<error>{error_msg}</error>\n")))
                                else:
                                    print(error_msg)
                            else:
                                response = result['result']
                                if session:
                                    session.output.write(to_formatted_text(HTML(f"<output>Chatbot: {response}</output>\n")))
                                else:
                                    print(f"Chatbot: {response}")
                                # Also speak the response
                                await tts.tts_speak(response)
                        except Exception as e:
                            error_msg = f"[ERROR] Failed to process conversation input: {e}"
                            if session:
                                session.output.write(to_formatted_text(HTML(f"<error>{error_msg}</error>\n")))
                            else:
                                print(error_msg)
                            log.exception("Conversation input error: %s", e)
                    else:
                        await tts.tts_speak(cmd)
                continue

            if session:
                session.output.write(to_formatted_text(HTML("<recording>Recording... press Enter again to stop.</recording>\n")))
                session.output.write("Recorder opening... inside it, press Ctrl+D to start/stop recording.\n")
                session.output.flush()
            else:
                print("Recording... press Enter again to stop.")
                print("Recorder opening... inside it, press Ctrl+D to start/stop recording.")
            
            text = await stt.run()
            if text:
                output_msg = f"You said: {text}"
                if session:
                    session.output.write(to_formatted_text(HTML(f"<output>{output_msg}</output>\n")))
                else:
                    print(output_msg)
                await tts.tts_speak(text)
            else:
                no_speech_msg = "(No speech detected)"
                if session:
                    session.output.write(to_formatted_text(HTML(f"<info>{no_speech_msg}</info>\n")))
                else:
                    print(no_speech_msg)

        except KeyboardInterrupt:
            if session:
                session.output.write("\nInterrupted. Bye.\n")
            else:
                print("\nInterrupted. Bye.")
            # Clean up resources
            if system_assistant:
                system_assistant.cleanup()
            if ai_assistant:
                ai_assistant.cleanup()
            return
        except EOFError:
            if session:
                session.output.write("\nEOF. Bye.\n")
            else:
                print("\nEOF. Bye.")
            # Clean up resources
            if system_assistant:
                system_assistant.cleanup()
            if ai_assistant:
                ai_assistant.cleanup()
            return
        except Exception as e:
            log.exception("CLI error: %s", e)
            error_msg = f"CLI error: {e}"
            if session:
                session.output.write(to_formatted_text(HTML(f"<error>{error_msg}</error>\n")))
            else:
                print(error_msg)
            # Clean up resources
            if system_assistant:
                system_assistant.cleanup()
            if ai_assistant:
                ai_assistant.cleanup()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except RuntimeError:
        # In case of nested event loop (e.g., in some shells), fallback
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main())
