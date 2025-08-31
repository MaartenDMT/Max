from ai_tools.ai_music_generation import (
    MusicLoopGenerator,  # Assuming this is the tool we just created
)


class MusicCreationAgent:
    def __init__(self):
        """
        Initialize the agent with a MusicLoopGenerator tool.
        """
        self.loop_generator = MusicLoopGenerator()

    def handle_user_request(self, user_input):
        """
        Handle user input by processing the request and determining what kind of music loop to generate.
        """
        # Parse the user input to extract key parameters (e.g., BPM, genre, duration)
        prompt, bpm, duration = self.parse_user_input(user_input)

        # Validate extracted parameters
        if not prompt or not prompt.strip():
            return {
                "status": "error",
                "message": "Missing or invalid prompt/genre in request.",
            }
        if bpm is None or not isinstance(bpm, int) or bpm < 40 or bpm > 240:
            return {
                "status": "error",
                "message": "BPM must be an integer between 40 and 240.",
            }

        if prompt and bpm:
            # Use the MusicLoopGenerator tool to generate the loop
            # Ensure duration is an integer, default to 30 if None
            if duration is None:
                actual_duration = 30
            else:
                # clamp duration into safe bounds
                try:
                    actual_duration = int(duration)
                except Exception:
                    actual_duration = 30
                actual_duration = max(5, min(actual_duration, 300))

            # If the underlying generator is unavailable (optional dependency missing), fail fast
            try:
                generator_available = getattr(self.loop_generator, "model", None) is not None
            except Exception:
                generator_available = False
            if not generator_available:
                return {
                    "status": "error",
                    "message": "Music generator is unavailable (optional dependency missing).",
                }
            loop_file = self.loop_generator.generate_loop(
                prompt=prompt, bpm=bpm, duration=actual_duration
            )
            if loop_file:
                return {
                    "status": "success",
                    "message": f"Music loop generated: {loop_file}",
                    "file_path": loop_file,
                }
            else:
                return {"status": "error", "message": "Failed to generate music loop."}
        else:
            return {
                "status": "error",
                "message": "Sorry, I couldn't understand your request. Please provide a valid genre and BPM.",
            }

    def parse_user_input(self, user_input):
        """
        Extracts the genre, BPM, and duration from the user input.
        Assumes the user input is a string in the form 'Generate a 140 BPM hip hop beat for 30 seconds'.
        """
        import re

        if not isinstance(user_input, str) or not user_input.strip():
            return None, None, None

        # Case-insensitive, non-greedy prompt; stop before 'for <n> seconds' if present
        pattern = (
            r"(?i)"  # case-insensitive
            r"(?P<bpm>\d+)\s*bpm\s*"
            r"(?P<prompt>[a-z0-9\s,\-/'&()\.]+?)(?=\s+for\s+\d+\s*seconds?\b|$)"
            r"(?:\s+for\s+(?P<duration>\d+)\s*seconds?\b)?"
        )
        match = re.search(pattern, user_input)

        if match:
            try:
                bpm = int(match.group("bpm"))
            except Exception:
                bpm = None
            prompt = (match.group("prompt") or "").strip()
            try:
                duration = (
                    int(match.group("duration")) if match.group("duration") else 30
                )
            except Exception:
                duration = 30
            return prompt, bpm, duration
        else:
            return None, None, None


# Example usage (removed interactive parts for API readiness)
# if __name__ == "__main__":
#     agent = MusicCreationAgent()

#     # Simulated user input
#     user_input = "Generate a 160 BPM hip hop beat for 40 seconds"

#     # Process user request
#     result = agent.handle_user_request(user_input)
#     print(result)
