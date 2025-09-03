import wave

import numpy as np
import sounddevice as sd


def record_audio(duration, filename):
    # Set recording parameters
    fs = 44100  # Sample rate (Hz)
    seconds = duration  # Recording duration (s)

    print("Recording...")
    recording = sd.rec(int(seconds * fs), samplerate=fs, channels=2)  # Stereo recording
    sd.wait()
    print("Recording finished.")

    # Save the recording as a wav file
    wave_file = wave.open(filename, "wb")
    wave_file.setnchannels(2)
    wave_file.setsampwidth(2 * np.dtypes.float32.itemsize)
    wave_file.setframerate(fs)
    wave_file.writeframes(np.float32(recording).tobytes())
    wave_file.close()


def play_audio(filename):
    # Load the audio file
    wav = wave.open(filename, "rb")

    # Set parameters
    nchannels = wav.getnChannels()
    sampleWidth = wav.getsampwidth()
    fs = wav.getframerate()
    data = np.frombuffer(wav.readframes(wav.getnframes()), dtype=np.int16)

    print("Playing...")
    sd.play(data, fs)
    sd.wait()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Record and playback audio.")
    parser.add_argument(
        "--record", action="store_true", help="Record audio (default: False)"
    )
    parser.add_argument(
        "--playback",
        action="store_true",
        help="Playback recorded audio (default: False)",
    )
    parser.add_argument(
        "--duration", type=float, default=10.0, help="Recording duration in seconds"
    )
    parser.add_argument(
        "--Filename", default="recording.wav", help="File name to save recording"
    )

    args = parser.parse_args()

    if args.record:
        record_audio(args.duration, args.Filename)
    elif args.playback:
        play_audio(args.Filename)
