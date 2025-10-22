"""
Free Text-to-Speech Service for TURN Platform
Supports multiple FREE TTS providers: gTTS, pyttsx3, and edge-tts
"""
import os
import asyncio
import tempfile
from typing import Optional, Dict, Any, List
from enum import Enum
import logging
from pathlib import Path

# Free TTS imports
try:
    from gtts import gTTS
except ImportError:
    gTTS = None

try:
    import pyttsx3
except ImportError:
    pyttsx3 = None

try:
    import edge_tts
except ImportError:
    edge_tts = None

from app.core.config import settings


class TTSProvider(Enum):
    """Available TTS providers."""
    GTTS = "gtts"          # Google TTS (free with internet)
    PYTTSX3 = "pyttsx3"    # Offline TTS (completely free)
    EDGE_TTS = "edge_tts"  # Microsoft Edge TTS (free)


class TTSService:
    """
    Free Text-to-Speech service using multiple providers.
    Automatically falls back to available providers.
    """
    
    def __init__(self, preferred_provider: TTSProvider = TTSProvider.GTTS):
        """Initialize TTS service with preferred provider."""
        self.preferred_provider = preferred_provider
        self.logger = logging.getLogger(__name__)
        self.audio_dir = Path(settings.media_root) / "audio" / "tts"
        self.audio_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize available providers
        self.providers = self._init_providers()
        
    def _init_providers(self) -> Dict[TTSProvider, bool]:
        """Check which TTS providers are available."""
        providers = {}
        
        # Google TTS (requires internet)
        if gTTS:
            providers[TTSProvider.GTTS] = True
            self.logger.info("Google TTS (gTTS) available")
        else:
            providers[TTSProvider.GTTS] = False
            self.logger.warning("Google TTS not available - install with: pip install gtts")
            
        # pyttsx3 (offline)
        if pyttsx3:
            providers[TTSProvider.PYTTSX3] = True
            self.logger.info("pyttsx3 (offline TTS) available")
        else:
            providers[TTSProvider.PYTTSX3] = False
            self.logger.warning("pyttsx3 not available - install with: pip install pyttsx3")
            
        # Edge TTS (requires internet)
        if edge_tts:
            providers[TTSProvider.EDGE_TTS] = True
            self.logger.info("Edge TTS available")
        else:
            providers[TTSProvider.EDGE_TTS] = False
            self.logger.warning("Edge TTS not available - install with: pip install edge-tts")
            
        return providers
    
    def get_available_provider(self) -> Optional[TTSProvider]:
        """Get the first available TTS provider."""
        if self.providers.get(self.preferred_provider, False):
            return self.preferred_provider
            
        # Fallback order: gTTS -> Edge TTS -> pyttsx3
        for provider in [TTSProvider.GTTS, TTSProvider.EDGE_TTS, TTSProvider.PYTTSX3]:
            if self.providers.get(provider, False):
                return provider
        return None
    
    async def generate_speech(
        self,
        text: str,
        voice: str = "default",
        speed: float = 1.0,
        language: str = "en"
    ) -> Optional[Dict[str, Any]]:
        """
        Generate speech from text using available TTS provider.
        
        Args:
            text: Text to convert to speech
            voice: Voice type (provider-specific)
            speed: Speech speed (0.5-2.0)
            language: Language code (e.g., 'en', 'es', 'fr')
            
        Returns:
            Dict with audio file path and metadata
        """
        provider = self.get_available_provider()
        if not provider:
            self.logger.error("No TTS providers available")
            return None
            
        try:
            if provider == TTSProvider.GTTS:
                return await self._generate_gtts(text, language, speed)
            elif provider == TTSProvider.EDGE_TTS:
                return await self._generate_edge_tts(text, voice, speed, language)
            elif provider == TTSProvider.PYTTSX3:
                return await self._generate_pyttsx3(text, voice, speed)
                
        except Exception as e:
            self.logger.error(f"TTS generation failed with {provider}: {e}")
            return None
    
    async def _generate_gtts(self, text: str, language: str, speed: float) -> Dict[str, Any]:
        """Generate speech using Google TTS (free)."""
        try:
            # Adjust speed by modifying text (limited control)
            if speed < 0.8:
                # Slow down by adding periods
                text = text.replace(" ", "... ")
            elif speed > 1.2:
                # Speed up by removing some punctuation
                text = text.replace(", ", " ").replace(". ", " ")
            
            tts = gTTS(text=text, lang=language, slow=(speed < 0.9))
            
            # Generate unique filename
            audio_filename = f"gtts_{hash(text)}_{language}.mp3"
            audio_path = self.audio_dir / audio_filename
            
            # Save audio file
            tts.save(str(audio_path))
            
            return {
                "provider": "gtts",
                "file_path": str(audio_path),
                "file_url": f"/media/audio/tts/{audio_filename}",
                "duration_seconds": len(text) * 0.1,  # Rough estimate
                "language": language,
                "voice": "default",
                "speed": speed
            }
            
        except Exception as e:
            raise Exception(f"Google TTS failed: {e}")
    
    async def _generate_edge_tts(
        self, 
        text: str, 
        voice: str, 
        speed: float, 
        language: str
    ) -> Dict[str, Any]:
        """Generate speech using Microsoft Edge TTS (free)."""
        try:
            # Map language to Edge TTS voices
            voice_map = {
                "en": "en-US-JennyNeural",
                "es": "es-ES-ElviraNeural", 
                "fr": "fr-FR-DeniseNeural",
                "de": "de-DE-KatjaNeural"
            }
            
            edge_voice = voice_map.get(language, "en-US-JennyNeural")
            if voice != "default":
                edge_voice = voice
            
            # Adjust speed for Edge TTS
            speed_percent = f"{int(speed * 100)}%"
            
            # Generate unique filename
            audio_filename = f"edge_{hash(text)}_{language}.wav"
            audio_path = self.audio_dir / audio_filename
            
            # Create Edge TTS communication
            communicate = edge_tts.Communicate(text, edge_voice, rate=speed_percent)
            await communicate.save(str(audio_path))
            
            return {
                "provider": "edge_tts",
                "file_path": str(audio_path),
                "file_url": f"/media/audio/tts/{audio_filename}",
                "duration_seconds": len(text) * 0.08,  # Rough estimate
                "language": language,
                "voice": edge_voice,
                "speed": speed
            }
            
        except Exception as e:
            raise Exception(f"Edge TTS failed: {e}")
    
    async def _generate_pyttsx3(self, text: str, voice: str, speed: float) -> Dict[str, Any]:
        """Generate speech using pyttsx3 (offline, free)."""
        try:
            # Initialize pyttsx3 engine
            engine = pyttsx3.init()
            
            # Set voice properties
            voices = engine.getProperty('voices')
            if voices and voice != "default":
                for v in voices:
                    if voice.lower() in v.name.lower():
                        engine.setProperty('voice', v.id)
                        break
            
            # Set speed (words per minute)
            engine.setProperty('rate', int(200 * speed))
            
            # Generate unique filename
            audio_filename = f"pyttsx3_{hash(text)}.wav"
            audio_path = self.audio_dir / audio_filename
            
            # Save to file
            engine.save_to_file(text, str(audio_path))
            engine.runAndWait()
            
            return {
                "provider": "pyttsx3",
                "file_path": str(audio_path),
                "file_url": f"/media/audio/tts/{audio_filename}",
                "duration_seconds": len(text) * 0.12,  # Rough estimate
                "language": "en",  # pyttsx3 is primarily English
                "voice": voice,
                "speed": speed
            }
            
        except Exception as e:
            raise Exception(f"pyttsx3 failed: {e}")
    
    async def generate_ai_lesson_audio(
        self,
        lesson_text: str,
        lesson_type: str = "coaching",
        user_level: str = "beginner"
    ) -> Optional[Dict[str, Any]]:
        """
        Generate audio for AI PM Teacher lessons.
        
        Args:
            lesson_text: The lesson content to convert to speech
            lesson_type: Type of lesson (coaching, feedback, guidance)
            user_level: User experience level for voice tone
            
        Returns:
            Audio file info with lesson metadata
        """
        # Adjust voice characteristics based on lesson type and user level
        speed = 0.9 if user_level == "beginner" else 1.1
        voice = "default"
        
        # Generate the audio
        audio_result = await self.generate_speech(
            text=lesson_text,
            voice=voice,
            speed=speed,
            language="en"
        )
        
        if audio_result:
            audio_result.update({
                "lesson_type": lesson_type,
                "user_level": user_level,
                "generated_at": asyncio.get_event_loop().time()
            })
            
        return audio_result
    
    def get_supported_voices(self, provider: TTSProvider = None) -> List[str]:
        """Get list of supported voices for a provider."""
        provider = provider or self.get_available_provider()
        
        if provider == TTSProvider.GTTS:
            return ["default"]
        elif provider == TTSProvider.EDGE_TTS:
            return [
                "en-US-JennyNeural", "en-US-GuyNeural",
                "en-GB-LibbyNeural", "en-AU-NatashaNeural"
            ]
        elif provider == TTSProvider.PYTTSX3:
            try:
                engine = pyttsx3.init()
                voices = engine.getProperty('voices')
                return [v.name for v in voices] if voices else ["default"]
            except:
                return ["default"]
        
        return ["default"]
    
    def get_supported_languages(self, provider: TTSProvider = None) -> List[str]:
        """Get list of supported languages for a provider."""
        provider = provider or self.get_available_provider()
        
        if provider == TTSProvider.GTTS:
            return ["en", "es", "fr", "de", "it", "pt", "ru", "ja", "ko", "zh"]
        elif provider == TTSProvider.EDGE_TTS:
            return ["en", "es", "fr", "de", "it", "pt", "ja", "ko", "zh"]
        elif provider == TTSProvider.PYTTSX3:
            return ["en"]  # Primarily English
            
        return ["en"]


# Global TTS service instance
tts_service = TTSService()