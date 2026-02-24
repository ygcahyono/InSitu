"""
Video subtitle extraction module for InSitu vocabulary app.
Extracts speech from video files using OpenAI Whisper (local).
"""

import hashlib
import os
import shutil
import tempfile

import whisper

# Cache the model so it only loads once per session
_whisper_model = None

# Expected SHA256 checksums for each model size (from whisper's _MODELS URLs)
_MODEL_CHECKSUMS = {
    "tiny": "65147644a518d12f04e32d6f3b26facc3f8dd46e5390956a9424a650c0ce22b9",
    "base": "ed3a0b6b1c0edf879ad9b11b1af5a0e6ab5db9205f891f668f8b0e6c6326e34e",
    "small": "9ecf779972d90ba49c06d968637d720dd632c55bbf19d441fb42bf17a411e794",
    "medium": "345ae4da62f9b3d59415adc60127b97c714f32e89e936602e85993674d08dcb1",
    "large": "e5b1a55b89c1367dacf97e3e19bfd829a01529dbfdeefa8caeb59b3f1b81dadb",
    "turbo": "aff26ae408abcba5fbf8813c21e62b0941638c5f6eebfb145be0c9839262a19a",
}


def _ensure_model_integrity(model_size: str = "medium"):
    """
    Check the cached Whisper model file for corruption before loading.

    If the file exists but has an incorrect SHA256 checksum (e.g. from an
    interrupted download), delete it so whisper.load_model() downloads a
    fresh copy exactly once rather than re-downloading on every call.
    """
    cache_dir = os.path.join(os.path.expanduser("~"), ".cache", "whisper")
    model_file = os.path.join(cache_dir, f"{model_size}.pt")

    if not os.path.isfile(model_file):
        return  # No cached file; whisper will download it fresh

    expected_sha256 = _MODEL_CHECKSUMS.get(model_size)
    if expected_sha256 is None:
        return  # Unknown model size; let whisper handle it

    sha256 = hashlib.sha256()
    with open(model_file, "rb") as f:
        while chunk := f.read(8192):
            sha256.update(chunk)

    if sha256.hexdigest() != expected_sha256:
        os.remove(model_file)


def _get_whisper_model(model_size: str = "medium"):
    """
    Load and cache the Whisper model.

    Validates the cached model file integrity before loading.
    If the cached file is corrupt, it is deleted so Whisper can
    re-download a clean copy.

    Args:
        model_size: Whisper model size (tiny, base, small, medium, large)

    Returns:
        Loaded Whisper model
    """
    global _whisper_model
    if _whisper_model is None:
        _ensure_model_integrity(model_size)
        _whisper_model = whisper.load_model(model_size)
    return _whisper_model


def extract_audio_from_video(video_path: str) -> str:
    """
    Extract the audio track from a video file as a temporary WAV file.

    Args:
        video_path: Path to the video file

    Returns:
        Path to the extracted audio WAV file
    """
    from moviepy import VideoFileClip

    audio_path = video_path.rsplit(".", 1)[0] + ".wav"

    video_clip = VideoFileClip(video_path)
    video_clip.audio.write_audiofile(audio_path, logger=None)
    video_clip.close()

    return audio_path


def transcribe_audio(audio_path: str, model_size: str = "medium") -> str:
    """
    Transcribe an audio file to text using Whisper.

    Args:
        audio_path: Path to the audio file
        model_size: Whisper model size to use

    Returns:
        Transcribed text
    """
    model = _get_whisper_model(model_size)
    result = model.transcribe(audio_path)
    return result["text"].strip()


def _check_ffmpeg():
    """
    Check if FFmpeg is available on the system.

    Raises:
        FileNotFoundError: If FFmpeg is not found in PATH.
    """
    if shutil.which("ffmpeg") is None:
        raise FileNotFoundError("FFmpeg not found")


def extract_subtitles_from_video(uploaded_file) -> tuple[bool, str]:
    """
    Main entry point: extract subtitles/speech from an uploaded video file.

    Takes a Streamlit UploadedFile, saves it temporarily, extracts audio,
    transcribes with Whisper, and returns the text.

    Args:
        uploaded_file: Streamlit UploadedFile object

    Returns:
        tuple: (success: bool, text_or_error: str)
    """
    # Check FFmpeg FIRST before downloading/loading the Whisper model
    # to avoid a 1.4GB download that gets wasted if FFmpeg is missing.
    try:
        _check_ffmpeg()
    except FileNotFoundError:
        return False, (
            "FFmpeg is not installed on your system.\n\n"
            "**To install on macOS:**\n"
            "```\nbrew install ffmpeg\n```\n\n"
            "After installation, restart the app."
        )

    temp_video_path = None
    temp_audio_path = None

    try:
        # Save uploaded video to a temporary file
        suffix = os.path.splitext(uploaded_file.name)[1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(uploaded_file.read())
            temp_video_path = tmp.name

        # Extract audio from video
        temp_audio_path = extract_audio_from_video(temp_video_path)

        # Transcribe audio with Whisper
        transcribed_text = transcribe_audio(temp_audio_path)

        if not transcribed_text:
            return False, (
                "No speech could be detected in this video. "
                "Please try a video with clearer audio."
            )

        return True, transcribed_text

    except Exception as e:
        return False, f"Error processing video: {str(e)}"

    finally:
        # Clean up temporary files
        if temp_video_path and os.path.exists(temp_video_path):
            os.unlink(temp_video_path)
        if temp_audio_path and os.path.exists(temp_audio_path):
            os.unlink(temp_audio_path)
