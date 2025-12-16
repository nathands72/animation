"""Video Assembly Agent for compiling media into final video."""

import logging
from typing import Dict, Any, List, Optional
from pathlib import Path

from config import get_config
from tools.video_tool import VideoProcessingTool
from utils.helpers import get_temp_path, get_output_path

logger = logging.getLogger(__name__)


class VideoAssemblyAgent:
    """Agent for assembling final video with narration and music."""
    
    def __init__(self):
        """Initialize video assembly agent."""
        self.config = get_config()
        self.video_tool = VideoProcessingTool()
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
                return self._generate_elevenlabs_narration(story, output_path)
            else:
                return self._generate_gtts_narration(story, output_path)
            
        except Exception as e:
            logger.error(f"Error generating narration: {e}")
            return None
    
    def _generate_elevenlabs_narration(
        self,
        story: str,
        output_path: Path
    ) -> Optional[Path]:
        """Generate narration using ElevenLabs."""
        try:
            from elevenlabs import generate, save
            
            voice_id = self.config.tts.voice_id or "21m00Tcm4TlvDq8ikWAM"  # Default voice
            
            audio = generate(
                text=story,
                voice=voice_id,
                model="eleven_monolingual_v1"
            )
            
            save(audio, str(output_path))
            logger.info(f"Narration generated: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error with ElevenLabs: {e}")
            return self._generate_gtts_narration(story, output_path)
    
    def _generate_gtts_narration(
        self,
        story: str,
        output_path: Path
    ) -> Optional[Path]:
        """Generate narration using gTTS."""
        try:
            from gtts import gTTS
            
            logger.info("Generating narration with gTTS...")
            tts = gTTS(text=story, lang=self.config.tts.language, slow=False)
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
    
    def get_background_music(
        self,
        duration_seconds: float
    ) -> Optional[Path]:
        """
        Get background music file (royalty-free, child-appropriate).
        
        Args:
            duration_seconds: Required duration in seconds
            
        Returns:
            Path to music file, or None if not available
        """
        # In a production system, you would:
        # 1. Use a royalty-free music API (e.g., Free Music Archive, YouTube Audio Library)
        # 2. Download appropriate child-friendly music
        # 3. Store it locally or cache it
        
        # For now, return None (music is optional)
        logger.info("Background music not implemented (optional feature)")
        return None
    
    def assemble_video(
        self,
        scene_images: List[Path],
        script_segments: List[Dict[str, Any]],
        story: str,
        context: Dict[str, Any],
        character_descriptions: Optional[Dict[str, Dict[str, Any]]] = None,
        output_path: Optional[Path] = None,
        workflow_id: Optional[str] = None
    ) -> Optional[Path]:
        """
        Assemble final video from scene images, narration, and music.
        
        Args:
            scene_images: List of paths to scene images
            script_segments: List of scene segments with durations
            story: Generated story text
            context: Context dictionary
            character_descriptions: Optional character descriptions
            output_path: Optional output path for final video
            workflow_id: Optional workflow ID for filename
            
        Returns:
            Path to final video file, or None if assembly failed
        """
        try:
            logger.info("Assembling final video")
            
            # Filter out None images
            valid_images = [img for img in scene_images if img and Path(img).exists()]
            
            if not valid_images:
                logger.error("No valid scene images provided")
                return None
            
            # Get durations from script segments
            durations = []
            for segment in script_segments:
                durations.append(segment.get("duration_seconds", 5.0))
            
            # Ensure durations match images
            while len(durations) < len(valid_images):
                durations.append(5.0)  # Default duration
            
            durations = durations[:len(valid_images)]
            
            # Create video from images
            logger.info("Creating video from scene images")
            video_path = self.video_tool.create_video_from_images(
                image_paths=valid_images,
                durations=durations,
                fps=self.config.video.fps,
                transition_duration=self.config.video.transition_duration
            )
            
            if not video_path:
                logger.error("Failed to create video from images")
                return None
            
            # Generate narration if enabled
            narration_path = None
            preferences = context.get("preferences", {})
            if preferences.get("narration", True):
                logger.info("Generating narration")
                narration_path = self.generate_narration(story)
            
            # Get background music if enabled
            music_path = None
            if preferences.get("music", True) and self.config.video.background_music:
                total_duration = sum(durations)
                music_path = self.get_background_music(total_duration)
            
            # Get moral message for end card
            moral_lesson = context.get("moral_lesson", "")
            
            # Determine final output path
            if output_path is None:
                if workflow_id:
                    filename = f"moral_video_{workflow_id}.mp4"
                else:
                    from datetime import datetime
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"moral_video_{timestamp}.mp4"
                output_path = get_output_path(filename)
            
            # Create final video with narration, music, and end card
            logger.info("Creating final video with narration and music")
            final_video_path = self.video_tool.create_final_video(
                video_path=video_path,
                narration_audio=narration_path,
                background_music=music_path,
                moral_message=moral_lesson,
                output_path=output_path
            )
            
            if not final_video_path:
                logger.error("Failed to create final video")
                return None
            
            logger.info(f"Final video created: {final_video_path}")
            return final_video_path
            
        except Exception as e:
            logger.error(f"Error assembling video: {e}")
            return None

