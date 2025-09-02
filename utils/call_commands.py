def get_system_commands(system_assistant):
    """Return a dictionary of system commands."""
    return {
        "time": system_assistant._tell_time_api,
        "open edge": system_assistant._open_edge_api,
        "what is your name": system_assistant._tell_name_api,
        "who are you": system_assistant._tell_name_api,
        "play": system_assistant._play_song_api,
        "joke": system_assistant._tell_joke_api,
        "minimize": system_assistant._minimize_api,
        "maximize": system_assistant._maximize_api,
        "close": system_assistant._close_window_api,
        "volume up": lambda query: system_assistant._adjust_volume_api("up"),
        "volume down": lambda query: system_assistant._adjust_volume_api("down"),
        "mute": lambda query: system_assistant._adjust_volume_api("mute"),
        "shutdown system": system_assistant._shutdown_api,
        "restart system": system_assistant._restart_api,
        "lock screen": system_assistant._lock_screen_api,
        "sleep system": system_assistant._sleep_api,
        "open app": system_assistant._open_app_api,
        "open file": system_assistant._open_file_api,
        "delete file": system_assistant._delete_file_api,
        "create folder": system_assistant._create_folder_api,
        "move file": system_assistant._move_file_api,
        "battery status": system_assistant._battery_status_api,
        "cpu usage": system_assistant._cpu_usage_api,
        "memory usage": system_assistant._memory_usage_api,
        "disk space": system_assistant._disk_space_api,
        "weather": system_assistant._get_weather_api,
        "set alarm": system_assistant._set_alarm_api,
        "take screenshot": system_assistant._take_screenshot_api,
        "calculate": system_assistant._calculate_api,
    }


def get_ai_commands(ai_assistant):
    """Return a dictionary of AI-related commands."""
    return {
        "summarize youtube": ai_assistant._summarize_youtube_api,
        "summarize website": ai_assistant._learn_site_api,
        "music loop": ai_assistant._make_loop_api,
        "research topic": ai_assistant._handle_research_api,
        "critique text": lambda query: ai_assistant.set_llm_mode("critique"),
        "reflect on text": lambda query: ai_assistant.set_llm_mode("reflecting"),
        "casual chat": lambda query: ai_assistant.set_llm_mode("casual"),
        "professional chat": lambda query: ai_assistant.set_llm_mode("professional"),
        "creative brainstorm": lambda query: ai_assistant.set_llm_mode("creative"),
        "analytical analysis": lambda query: ai_assistant.set_llm_mode("analytical"),
        "chat with": ai_assistant._start_conversation_mode,  # Start conversation with chatbot
        "write book": ai_assistant._handle_writer_task_api,  # Call the writer assistant to handle book writing
        "write story": ai_assistant._handle_writer_task_api,
        "create story": ai_assistant._handle_writer_task_api,
    }
