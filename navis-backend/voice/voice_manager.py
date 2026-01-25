"""
Voice Manager - Handles speech-to-text conversion
"""

import base64
import io
import speech_recognition as sr
from typing import Optional
from loguru import logger

class VoiceManager:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.microphone = None
        self._ready = True
        
    def is_ready(self) -> bool:
        """Check if voice manager is ready"""
        return self._ready
    
    async def speech_to_text(self, audio_data: str) -> str:
        """
        Convert base64 encoded audio to text
        
        Args:
            audio_data: Base64 encoded audio data
            
        Returns:
            Transcribed text
        """
        try:
            # Decode base64 audio data
            audio_bytes = base64.b64decode(audio_data)
            audio_file = io.BytesIO(audio_bytes)
            
            # Use speech recognition
            with sr.AudioFile(audio_file) as source:
                audio = self.recognizer.record(source)
                
            # Try Google Speech Recognition first (free tier)
            try:
                text = self.recognizer.recognize_google(audio)
                logger.info(f"Speech recognized: {text}")
                return text
                
            except sr.UnknownValueError:
                logger.warning("Could not understand audio")
                raise ValueError("Could not understand the audio")
                
            except sr.RequestError as e:
                logger.error(f"Speech recognition service error: {e}")
                # Fallback to offline recognition if available
                try:
                    text = self.recognizer.recognize_sphinx(audio)
                    logger.info(f"Offline speech recognized: {text}")
                    return text
                except:
                    raise ValueError("Speech recognition service unavailable")
                    
        except Exception as e:
            logger.error(f"Error in speech-to-text: {e}")
            raise ValueError(f"Speech processing failed: {str(e)}")
    
    def listen_from_microphone(self, timeout: int = 5) -> str:
        """
        Listen directly from microphone (for testing)
        
        Args:
            timeout: Listening timeout in seconds
            
        Returns:
            Transcribed text
        """
        try:
            if not self.microphone:
                self.microphone = sr.Microphone()
                
            with self.microphone as source:
                logger.info("Listening...")
                self.recognizer.adjust_for_ambient_noise(source)
                audio = self.recognizer.listen(source, timeout=timeout)
                
            text = self.recognizer.recognize_google(audio)
            logger.info(f"Microphone speech recognized: {text}")
            return text
            
        except sr.WaitTimeoutError:
            raise ValueError("Listening timeout - no speech detected")
        except sr.UnknownValueError:
            raise ValueError("Could not understand the speech")
        except Exception as e:
            logger.error(f"Microphone error: {e}")
            raise ValueError(f"Microphone processing failed: {str(e)}")
    
    def test_microphone(self) -> bool:
        """Test if microphone is working"""
        try:
            if not self.microphone:
                self.microphone = sr.Microphone()
            return True
        except Exception as e:
            logger.error(f"Microphone test failed: {e}")
            return False