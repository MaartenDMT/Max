def get_system_commands(system_assistant):
    """Return a dictionary of system commands."""
    return {
        "time": system_assistant._tell_time,
        "open edge": system_assistant._open_edge,
        "what is your name": system_assistant._tell_name,
        "who are you": system_assistant._tell_name,
        "play": system_assistant._play_song,
        "type": system_assistant._type_text,
        "joke": system_assistant._tell_joke,
        "minimize": system_assistant._minimize,
        "maximize": system_assistant._maximize,
        "close": system_assistant._close_window,
        "volume up": lambda query: system_assistant._adjust_volume("up"),
        "volume down": lambda query: system_assistant._adjust_volume("down"),
        "mute": lambda query: system_assistant._adjust_volume("mute"),
        "shutdown system": system_assistant._shutdown,
        "restart system": system_assistant._restart,
        "lock screen": system_assistant._lock_screen,
        "sleep system": system_assistant._sleep,
        "open app": system_assistant._open_app,
        "open file": system_assistant._open_file,
        "delete file": system_assistant._delete_file,
        "create folder": system_assistant._create_folder,
        "move file": system_assistant._move_file,
        "battery status": system_assistant._battery_status,
        "cpu usage": system_assistant._cpu_usage,
        "memory usage": system_assistant._memory_usage,
        "disk space": system_assistant._disk_space,
        "weather": system_assistant._get_weather,
        "set alarm": system_assistant._set_alarm,
        "take screenshot": system_assistant._take_screenshot,
        "calculate": system_assistant._calculate,
    }


def get_ai_commands(ai_assistant):
    """Return a dictionary of AI-related commands."""
    return {
        "summarize youtube": ai_assistant._summarize_youtube,
        "summarize website": ai_assistant._learn_site,
        "music loop": ai_assistant._make_loop,
        "research topic": ai_assistant._handle_research,
        "critique text": lambda query: ai_assistant.set_llm_mode("critique"),
        "reflect on text": lambda query: ai_assistant.set_llm_mode("reflecting"),
        "write book": ai_assistant._handle_writer_task,  # Call the writer assistant to handle book writing
        "write story": ai_assistant._handle_writer_task,
        "create story": ai_assistant._handle_writer_task,
    }
