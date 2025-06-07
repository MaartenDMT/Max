from ai_tools.ai_music_generation import (
    MusicLoopGenerator,
)  # Assuming this is the tool we just created


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

        if prompt and bpm:
            # Use the MusicLoopGenerator tool to generate the loop
            # Ensure duration is an integer, default to 30 if None
            actual_duration = duration if duration is not None else 30
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

        # Define a regex pattern to extract BPM, prompt (genre), and duration from the user input
        pattern = r"(?P<bpm>\d+)\s*BPM\s*(?P<prompt>[a-zA-Z\s]+)\s*(?:for\s*(?P<duration>\d+)\s*seconds)?"
        match = re.search(pattern, user_input)

        if match:
            bpm = int(match.group("bpm"))
            prompt = match.group("prompt").strip()
            duration = (
                int(match.group("duration")) if match.group("duration") else 30
            )  # Default duration to 30 seconds
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
