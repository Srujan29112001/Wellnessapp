"""
Audio Interface for Voice Interaction
Speech-to-Text (STT) and Text-to-Speech (TTS)
"""

import logging
from typing import Optional, Dict, Any
from pathlib import Path
import wave

import speech_recognition as sr
import pyttsx3
from gtts import gTTS
import soundfile as sf

logger = logging.getLogger(__name__)


class AudioInterface:
    """
    Voice interface with STT and TTS capabilities
    """

    def __init__(
        self,
        use_online_stt: bool = False,
        tts_engine: str = "pyttsx3"  # or "gtts"
    ):
        """
        Initialize audio interface

        Args:
            use_online_stt: Use online STT (Google) vs offline (Sphinx)
            tts_engine: TTS engine to use
        """
        self.use_online_stt = use_online_stt
        self.tts_engine_name = tts_engine

        # Initialize speech recognizer
        self.recognizer = sr.Recognizer()

        # Initialize TTS
        if tts_engine == "pyttsx3":
            try:
                self.tts_engine = pyttsx3.init()
                # Configure voice properties
                self.tts_engine.setProperty('rate', 150)  # Speed
                self.tts_engine.setProperty('volume', 0.9)  # Volume
                logger.info("Initialized pyttsx3 TTS engine")
            except Exception as e:
                logger.error(f"Could not initialize pyttsx3: {e}")
                self.tts_engine = None
        else:
            self.tts_engine = None  # Will use gTTS

    def transcribe_audio(
        self,
        audio_file_path: str,
        language: str = "en-US"
    ) -> Dict[str, Any]:
        """
        Transcribe audio file to text (Speech-to-Text)

        Args:
            audio_file_path: Path to audio file
            language: Language code

        Returns:
            Transcription result with text and confidence
        """
        try:
            # Load audio file
            with sr.AudioFile(audio_file_path) as source:
                audio_data = self.recognizer.record(source)

            # Transcribe
            if self.use_online_stt:
                # Use Google Speech Recognition
                text = self.recognizer.recognize_google(
                    audio_data,
                    language=language
                )
                method = "google"
            else:
                # Use offline Sphinx
                try:
                    text = self.recognizer.recognize_sphinx(audio_data)
                    method = "sphinx"
                except Exception as e:
                    logger.warning(f"Sphinx failed: {e}, falling back to Google")
                    text = self.recognizer.recognize_google(audio_data, language=language)
                    method = "google_fallback"

            logger.info(f"Transcribed audio using {method}: {text[:50]}...")

            return {
                "success": True,
                "text": text,
                "method": method,
                "language": language
            }

        except sr.UnknownValueError:
            logger.warning("Could not understand audio")
            return {
                "success": False,
                "error": "Could not understand audio",
                "text": ""
            }

        except sr.RequestError as e:
            logger.error(f"Speech recognition request error: {e}")
            return {
                "success": False,
                "error": f"Request error: {e}",
                "text": ""
            }

        except Exception as e:
            logger.error(f"Error transcribing audio: {e}")
            return {
                "success": False,
                "error": str(e),
                "text": ""
            }

    def transcribe_microphone(
        self,
        duration: Optional[int] = None,
        language: str = "en-US"
    ) -> Dict[str, Any]:
        """
        Transcribe from microphone input

        Args:
            duration: Recording duration in seconds (None for automatic)
            language: Language code

        Returns:
            Transcription result
        """
        try:
            with sr.Microphone() as source:
                logger.info("Listening...")

                # Adjust for ambient noise
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)

                # Record
                if duration:
                    audio_data = self.recognizer.record(source, duration=duration)
                else:
                    audio_data = self.recognizer.listen(source)

                logger.info("Processing audio...")

            # Transcribe
            if self.use_online_stt:
                text = self.recognizer.recognize_google(audio_data, language=language)
                method = "google"
            else:
                text = self.recognizer.recognize_sphinx(audio_data)
                method = "sphinx"

            logger.info(f"Transcribed: {text}")

            return {
                "success": True,
                "text": text,
                "method": method
            }

        except Exception as e:
            logger.error(f"Error recording/transcribing: {e}")
            return {
                "success": False,
                "error": str(e),
                "text": ""
            }

    def speak(
        self,
        text: str,
        save_to_file: Optional[str] = None,
        voice_gender: str = "female"
    ) -> bool:
        """
        Convert text to speech (Text-to-Speech)

        Args:
            text: Text to speak
            save_to_file: Optional path to save audio file
            voice_gender: Preferred voice gender

        Returns:
            Success status
        """
        try:
            if self.tts_engine_name == "pyttsx3" and self.tts_engine:
                # Use pyttsx3 (offline, real-time)

                # Select voice
                voices = self.tts_engine.getProperty('voices')
                if voice_gender == "female" and len(voices) > 1:
                    self.tts_engine.setProperty('voice', voices[1].id)
                elif voices:
                    self.tts_engine.setProperty('voice', voices[0].id)

                if save_to_file:
                    self.tts_engine.save_to_file(text, save_to_file)
                    self.tts_engine.runAndWait()
                else:
                    self.tts_engine.say(text)
                    self.tts_engine.runAndWait()

                logger.info("TTS complete (pyttsx3)")

            else:
                # Use gTTS (online, saved to file)
                if not save_to_file:
                    save_to_file = "/tmp/tts_output.mp3"

                tts = gTTS(text=text, lang='en', slow=False)
                tts.save(save_to_file)

                logger.info(f"TTS saved to {save_to_file}")

            return True

        except Exception as e:
            logger.error(f"Error in TTS: {e}")
            return False

    def create_guided_audio(
        self,
        script: str,
        output_path: str,
        add_pauses: bool = True
    ) -> bool:
        """
        Create guided audio session (meditation, breathing, etc.)

        Args:
            script: Guiding script with [PAUSE] markers
            output_path: Where to save audio
            add_pauses: Whether to add pauses at markers

        Returns:
            Success status
        """
        try:
            if add_pauses:
                # Process script to add actual pauses
                # Replace [PAUSE X] with silence
                import re

                segments = []
                parts = re.split(r'\[PAUSE (\d+)\]', script)

                for i, part in enumerate(parts):
                    if i % 2 == 0:  # Text
                        if part.strip():
                            # Generate speech for text
                            temp_file = f"/tmp/segment_{i}.mp3"
                            self.speak(part.strip(), save_to_file=temp_file)
                            segments.append(("speech", temp_file))
                    else:  # Pause duration
                        duration = int(part)
                        segments.append(("pause", duration))

                # Combine segments (would need audio processing library)
                # For now, just generate without pauses
                logger.warning("Pause processing not fully implemented, generating continuous audio")

            # Generate audio
            self.speak(script.replace('[PAUSE', '').replace(']', ''), save_to_file=output_path)

            logger.info(f"Guided audio created: {output_path}")
            return True

        except Exception as e:
            logger.error(f"Error creating guided audio: {e}")
            return False


# Singleton instance
_audio_interface: Optional[AudioInterface] = None


def get_audio_interface() -> AudioInterface:
    """Get or create audio interface singleton"""
    global _audio_interface
    if _audio_interface is None:
        _audio_interface = AudioInterface()
    return _audio_interface
