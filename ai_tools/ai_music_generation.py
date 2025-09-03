import asyncio  # Import asyncio for to_thread
import os

import numpy as np
import torch
import torchaudio
from einops import rearrange

# stable-audio-tools is large and optional; import lazily and provide clear errors
try:
    from stable_audio_tools import get_pretrained_model
    from stable_audio_tools.inference.generation import generate_diffusion_cond
    _STABLE_AUDIO_AVAILABLE = True
except Exception:  # pragma: no cover - optional dependency
    _STABLE_AUDIO_AVAILABLE = False


from utils.loggers import LoggerSetup


class MusicLoopGenerator:
    def __init__(self, model_name="stabilityai/stable-audio-open-1.0", device=None):
        log_setup = LoggerSetup()
        self.logger = log_setup.get_logger(
            "MusicLoopGenerator", "music_loop_generator.log"
        )
        self.logger.info("MusicLoopGenerator initialized with lazy loading.")
        """
        Initialize the music loop generator with lazy model loading.
        You can specify the model and the device (e.g., 'cuda' or 'cpu').
        """
        self.device = (
            device if device else ("cuda" if torch.cuda.is_available() else "cpu")
        )
        self.model_name = model_name
        self._model = None
        self._model_config = None

        # If stable-audio-tools is unavailable, degrade gracefully and log a warning.
        if not _STABLE_AUDIO_AVAILABLE:  # pragma: no cover - runtime path depends on install
            self.logger.warning(
                "stable-audio-tools not installed; MusicLoopGenerator disabled."
            )
            # sensible defaults for downstream code that might inspect these
            self._model_config = {"sample_rate": 44100, "sample_size": 1024}
            self._is_available = False
        else:
            self._is_available = True

    def _load_model(self):
        """Lazy load the model only when needed"""
        if not self._is_available:
            return False

        if self._model is None:
            self.logger.info(f"Lazy loading music generation model: {self.model_name}")
            try:
                # Load the pre-trained model
                self._model, self._model_config = get_pretrained_model(self.model_name)
                # Send the model to the selected device
                self._model = self._model.to(self.device)
                return True
            except Exception as e:
                self.logger.error(f"Failed to load music generation model: {str(e)}")
                self._is_available = False
                return False
        return True

    @property
    def model(self):
        """Property to access the model with lazy loading"""
        if self._model is None:
            self._load_model()
        return self._model

    @model.setter
    def model(self, value):
        # Allow tests to disable or inject a fake model
        self._model = value

    @property
    def model_config(self):
        """Property to access the model config with lazy loading"""
        if self._model_config is None and self._is_available:
            self._load_model()
        return self._model_config

    @property
    def sample_rate(self):
        """Property to access the sample rate"""
        return self.model_config["sample_rate"]

    @property
    def sample_size(self):
        """Property to access the sample size"""
        return self.model_config["sample_size"]

    async def generate_loop(  # Marked as async
        self, prompt, bpm=140, duration=30, output_dir="data/audio/loops/", seed=42
    ):
        """
        Generates a music loop based on the provided prompt and BPM asynchronously.

        Args:
        - prompt (str): Description of the loop (e.g., 'hip hop beat loop').
        - bpm (int): Beats per minute for the loop.
        - duration (int): Duration of the loop in seconds.
        - output_dir (str): Directory where the output audio file will be saved.
        - seed (int): Random seed for generation consistency.
        """
        # Lazy load the model if it hasn't been loaded yet
        if not self._load_model():
            return None
        # Create conditioning with the prompt and duration
        conditioning = {
            "prompt": f"{bpm} BPM {prompt} loop",
            "seconds_start": 0,
            "seconds_total": duration,
        }

        # Generate audio using the model - wrap blocking call
        output = await asyncio.to_thread(
            generate_diffusion_cond,
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

        # Rearrange and process the audio output - wrap blocking call
        output = await asyncio.to_thread(rearrange, output, "b d n -> d (b n)")
        output = await asyncio.to_thread(
            lambda: output.to(torch.float32)
            .div(torch.max(torch.abs(output)))
            .clamp(-1, 1)
            .mul(32767)
            .to(torch.int16)
            .cpu()
        )

        # Ensure the output directory exists - wrap blocking call
        if not await asyncio.to_thread(os.path.exists, output_dir):
            await asyncio.to_thread(os.makedirs, output_dir)

        # Save the audio file - wrap blocking call
        output_file = f"{output_dir}{bpm}_BPM_{prompt}.wav"
        await asyncio.to_thread(torchaudio.save, output_file, output, self.sample_rate)
        self.logger.info(f"Music loop saved: {output_file}")

        return output_file


# Example usage (removed interactive parts for API readiness)
# if __name__ == "__main__":
#     async def run_example():
#         generator = MusicLoopGenerator()
#         await generator.generate_loop(prompt="hip hop beat", bpm=160)
#     asyncio.run(run_example())
