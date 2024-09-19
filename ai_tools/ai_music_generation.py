import os

import numpy as np
import torch
import torchaudio
from einops import rearrange
from stable_audio_tools import get_pretrained_model
from stable_audio_tools.inference.generation import generate_diffusion_cond

from utils.loggers import LoggerSetup

log_setup = LoggerSetup()
app_logger = log_setup.get_logger("app_logger", "app.log")


class MusicLoopGenerator:
    def __init__(self, model_name="stabilityai/stable-audio-open-1.0", device=None):
        """
        Initialize the music loop generator with a pre-trained model.
        You can specify the model and the device (e.g., 'cuda' or 'cpu').
        """
        self.device = (
            device if device else ("cuda" if torch.cuda.is_available() else "cpu")
        )

        # Load the pre-trained model
        self.model, self.model_config = get_pretrained_model(model_name)
        self.sample_rate = self.model_config["sample_rate"]
        self.sample_size = self.model_config["sample_size"]

        # Send the model to the selected device
        self.model = self.model.to(self.device)

    def generate_loop(
        self, prompt, bpm=140, duration=30, output_dir="data/audio/loops/", seed=42
    ):
        """
        Generates a music loop based on the provided prompt and BPM.

        Args:
        - prompt (str): Description of the loop (e.g., 'hip hop beat loop').
        - bpm (int): Beats per minute for the loop.
        - duration (int): Duration of the loop in seconds.
        - output_dir (str): Directory where the output audio file will be saved.
        - seed (int): Random seed for generation consistency.
        """
        # Create conditioning with the prompt and duration
        conditioning = [
            {
                "prompt": f"{bpm} BPM {prompt} loop",
                "seconds_start": 0,
                "seconds_total": duration,
            }
        ]

        # Generate audio using the model
        output = generate_diffusion_cond(
            self.model,
            steps=100,
            cfg_scale=7,
            conditioning=conditioning,
            sample_size=self.sample_size,
            sigma_min=0.3,
            sigma_max=500,
            sampler_type="dpmpp-3m-sde",
            device=self.device,
            seed=seed if seed != -1 else np.random.randint(0, 2**32 - 1),
        )

        # Rearrange and process the audio output
        output = rearrange(output, "b d n -> d (b n)")
        output = (
            output.to(torch.float32)
            .div(torch.max(torch.abs(output)))
            .clamp(-1, 1)
            .mul(32767)
            .to(torch.int16)
            .cpu()
        )

        # Ensure the output directory exists
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # Save the audio file
        output_file = f"{output_dir}{bpm}_BPM_{prompt}.wav"
        torchaudio.save(output_file, output, self.sample_rate)
        print(f"Music loop saved: {output_file}")

        return output_file


# Example usage
if __name__ == "__main__":
    generator = MusicLoopGenerator()
    generator.generate_loop(prompt="hip hop beat", bpm=160)
