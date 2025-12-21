"""Audio processing tool for text-to-speech and audio generation."""

import logging
from typing import Dict, Any, List, Optional
from pathlib import Path

from config import get_config
from utils.helpers import get_temp_path

logger = logging.getLogger(__name__)


class AudioTool:
    """Tool for generating and processing audio files."""
    
    def __init__(self):
        """Initialize audio tool."""
        self.config = get_config()
        self.elevenlabs_available = False
        self._initialize_tts()
    
    def _initialize_tts(self):
        """Initialize text-to-speech client."""
        try:
            if self.config.tts.provider == "elevenlabs" and self.config.tts.api_key:
                from elevenlabs import generate, set_api_key
                set_api_key(self.config.tts.api_key)
                self.elevenlabs_available = True
                logger.info("ElevenLabs TTS initialized")
            else:
                self.elevenlabs_available = False
                logger.info("Using gTTS for text-to-speech")
        except ImportError:
            self.elevenlabs_available = False
            logger.warning("ElevenLabs not installed, using gTTS")
        except Exception as e:
            self.elevenlabs_available = False
            logger.warning(f"Error initializing ElevenLabs: {e}, using gTTS")
    
    def generate_narration(
        self,
        story: str,
        output_path: Optional[Path] = None
    ) -> Optional[Path]:
        """
        Generate narration audio from story text.
        
        Args:
            story: Story text to narrate
            output_path: Optional output path for audio file
            
        Returns:
            Path to narration audio file, or None if generation failed
        """
        try:
            logger.info("Generating narration audio")
            
            if output_path is None:
                output_path = get_temp_path("narration.mp3", "audio")
            
            if self.elevenlabs_available and self.config.tts.provider == "elevenlabs":
                return self.generate_elevenlabs_narration(story, output_path)
            else:
                return self.generate_gtts_narration(story, output_path)
            
        except Exception as e:
            logger.error(f"Error generating narration: {e}")
            return None
    
    def generate_elevenlabs_narration(
        self,
        text: str,
        output_path: Path
    ) -> Optional[Path]:
        """
        Generate narration using ElevenLabs.
        
        Args:
            text: Text to convert to speech
            output_path: Path to save audio file
            
        Returns:
            Path to generated audio file, or None if failed
        """
        try:
            from elevenlabs import generate, save
            
            voice_id = self.config.tts.voice_id or "21m00Tcm4TlvDq8ikWAM"  # Default voice
            
            audio = generate(
                text=text,
                voice=voice_id,
                model="eleven_monolingual_v1"
            )
            
            save(audio, str(output_path))
            logger.info(f"Narration generated: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error with ElevenLabs: {e}")
            return self.generate_gtts_narration(text, output_path)
    
    def generate_gtts_narration(
        self,
        text: str,
        output_path: Path
    ) -> Optional[Path]:
        """
        Generate narration using gTTS.
        
        Args:
            text: Text to convert to speech
            output_path: Path to save audio file
            
        Returns:
            Path to generated audio file, or None if failed
        """
        try:
            from gtts import gTTS
            
            logger.info("Generating narration with gTTS...")
            tts = gTTS(text=text, lang=self.config.tts.language, slow=False)
            tts.save(str(output_path))
            
            # Verify the file was created and has content
            if output_path.exists() and output_path.stat().st_size > 0:
                logger.info(f"Narration generated successfully: {output_path}")
                return output_path
            else:
                logger.error("gTTS created an empty file")
                return None
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error generating gTTS narration: {error_msg}")
            
            # Provide helpful context for common errors
            if "200" in error_msg or "OK" in error_msg:
                logger.error("gTTS received HTTP 200 but failed to process audio. This may be due to:")
                logger.error("  1. Network/firewall blocking Google TTS service")
                logger.error("  2. Rate limiting from Google")
                logger.error("  3. Corrupted gTTS installation")
                logger.error("Solutions:")
                logger.error("  - Try: pip install --upgrade gtts")
                logger.error("  - Use ElevenLabs instead (set ELEVENLABS_API_KEY in .env)")
                logger.error("  - Disable narration temporarily in preferences")
            
            return None
    
    def get_audio_duration(self, audio_path: Path) -> float:
        """
        Get duration of audio file in seconds.
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Duration in seconds, or 0.0 if failed
        """
        try:
            from moviepy.editor import AudioFileClip
            
            audio_clip = AudioFileClip(str(audio_path))
            duration = audio_clip.duration
            audio_clip.close()
            
            return duration
        except Exception as e:
            logger.error(f"Error getting audio duration: {e}")
            return 0.0
    
    def generate_segment_audio_files(
        self,
        script_segments: List[Dict[str, Any]],
        story: str,
        story_chunks: List[str],
        audio_output_dir: Path,
        get_segment_narration_text_fn: callable
    ) -> tuple[List[Optional[Path]], List[float]]:
        """
        Generate audio files for video segments using hybrid narration approach.
        
        This function generates narration audio for each segment, preferring segment-specific
        narration when available, falling back to story chunks for complete coverage.
        
        Args:
            script_segments: List of scene segments with optional narration
            story: Complete story text
            story_chunks: Pre-split story chunks (one per segment)
            audio_output_dir: Directory to save audio files
            get_segment_narration_text_fn: Function to get segment narration text
            
        Returns:
            Tuple of (segment_audio_paths, durations) where:
                - segment_audio_paths: List of paths to generated audio files (or None)
                - durations: List of durations in seconds for each segment
        """
        segment_audio_paths = []
        durations = []
        
        logger.info("Generating per-segment narration with hybrid approach")
        
        for i, (segment, story_chunk) in enumerate(zip(script_segments, story_chunks)):
            # Use hybrid approach: prefer segment narration, fallback to story chunk
            narration_text = get_segment_narration_text_fn(
                segment=segment,
                story_chunk=story_chunk,
                segment_index=i
            )
            
            if not narration_text.strip():
                logger.warning(f"Segment {i + 1} has no narration text, using default duration")
                segment_audio_paths.append(None)
                durations.append(segment.get("duration_seconds", 5.0))
                continue
            
            # Generate narration audio
            scene_number = segment.get("scene_number", i + 1)
            output_path = audio_output_dir / f"segment_{scene_number}_narration.mp3"
            
            logger.info(f"Generating narration for segment {scene_number}: {narration_text[:50]}...")
            
            # Generate narration using appropriate TTS
            if self.elevenlabs_available and self.config.tts.provider == "elevenlabs":
                audio_path = self.generate_elevenlabs_narration(narration_text, output_path)
            else:
                audio_path = self.generate_gtts_narration(narration_text, output_path)
            
            if audio_path:
                # Use actual audio duration
                duration = self.get_audio_duration(audio_path)
                if duration > 0:
                    segment_audio_paths.append(audio_path)
                    durations.append(duration)
                    logger.info(f"Segment {scene_number}: {duration:.2f}s (from audio)")
                else:
                    logger.warning(f"Invalid audio duration for segment {scene_number}, using default")
                    segment_audio_paths.append(None)
                    durations.append(segment.get("duration_seconds", 5.0))
            else:
                # No narration audio generated, use default duration
                logger.warning(f"Failed to generate narration for segment {scene_number}")
                segment_audio_paths.append(None)
                durations.append(segment.get("duration_seconds", 5.0))
        
        return segment_audio_paths, durations
