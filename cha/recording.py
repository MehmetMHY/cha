import tempfile
import time
import uuid
import os

from cha import colors, config, loading


def _lazy_import_recording_deps():
    global np, sd, write, OpenAI
    try:
        import numpy as np
        import sounddevice as sd
        from scipy.io.wavfile import write
        from openai import OpenAI

        return True
    except ImportError:
        return False


def record_get_text(client=None):
    if not _lazy_import_recording_deps():
        print(
            colors.red(
                "Missing dependencies for recording. Install: openai, scipy, sounddevice"
            )
        )
        return None

    sample_rate = 44100
    tmpdir = tempfile.mkdtemp()
    filepath = os.path.join(tmpdir, f"{uuid.uuid4()}.wav")

    try:
        frames = []
        flag = {"recording": True}

        def callback(indata, frames_count, time_info, status):
            if flag["recording"]:
                frames.append(indata.copy())

        with sd.InputStream(samplerate=sample_rate, channels=1, callback=callback):
            loading.start_loading("Recording... Press any key to stop", "dots")

            try:
                import sys
                import tty
                import termios

                old_settings = termios.tcgetattr(sys.stdin)
                tty.setraw(sys.stdin.fileno())
                sys.stdin.read(1)
                termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
            except (KeyboardInterrupt, EOFError, ImportError):
                pass
            finally:
                flag["recording"] = False
                loading.stop_loading()

        if not frames:
            print(colors.red("No audio recorded"))
            return None

        audio = np.concatenate(frames, axis=0)
        write(filepath, sample_rate, audio)

        if config.TEXT_TO_SPEECH_MODEL == "local":
            from cha import utils

            loading.start_loading("Processing audio", "basic")
            text = utils.transcribe_file(filepath)
            loading.stop_loading()
            if isinstance(text, dict):
                print(
                    colors.red(
                        f"Local transcription error: {text.get('error', 'Unknown error')}"
                    )
                )
                return None
            # remove timestamps and clean up text for recording
            import re

            cleaned_text = re.sub(r"\[\d+\.\d+s -> \d+\.\d+s\]\s*", "", text)
            return cleaned_text.strip()
        else:
            if client is None:
                client = OpenAI()

            with open(filepath, "rb") as f:
                loading.start_loading("Processing audio", "basic")
                resp = client.audio.transcriptions.create(
                    model=config.TEXT_TO_SPEECH_MODEL, file=f, response_format="json"
                )
                loading.stop_loading()

            text = resp.text
            return text

    except Exception as e:
        print(colors.red(f"Recording error: {e}"))
        return None
    finally:
        import shutil

        shutil.rmtree(tmpdir, ignore_errors=True)
