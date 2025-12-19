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
    
    def _get_audio_duration(self, audio_path: Path) -> float:
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
    
    def generate_segment_narration(
        self,
        segment: Dict[str, Any],
        segment_index: int,
        output_dir: Path
    ) -> Optional[Dict[str, Any]]:
        """
        Generate narration for a single segment.
        
        Args:
            segment: Scene segment dictionary
            segment_index: Index of the segment (0-based)
            output_dir: Directory to save audio file
            
        Returns:
            Dict with 'audio_path' and 'duration', or None if no narration
        """
        try:
            # Get narration text from segment
            narration_text = segment.get("narration") or segment.get("dialogue") or ""
            
            # Skip if no narration text
            if not narration_text or not narration_text.strip():
                logger.info(f"Segment {segment_index + 1} has no narration, skipping")
                return None
            
            # Create output path
            scene_number = segment.get("scene_number", segment_index + 1)
            output_path = output_dir / f"segment_{scene_number}_narration.mp3"
            
            logger.info(f"Generating narration for segment {scene_number}: {narration_text[:50]}...")
            
            # Generate narration using appropriate TTS
            if self.elevenlabs_available and self.config.tts.provider == "elevenlabs":
                audio_path = self._generate_elevenlabs_narration(narration_text, output_path)
            else:
                audio_path = self._generate_gtts_narration(narration_text, output_path)
            
            if not audio_path:
                logger.warning(f"Failed to generate narration for segment {scene_number}")
                return None
            
            # Get actual audio duration
            duration = self._get_audio_duration(audio_path)
            
            if duration <= 0:
                logger.warning(f"Invalid audio duration for segment {scene_number}")
                return None
            
            logger.info(f"Segment {scene_number} narration generated: {duration:.2f}s")
            
            return {
                "audio_path": audio_path,
                "duration": duration
            }
            
        except Exception as e:
            logger.error(f"Error generating segment narration: {e}")
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
            logger.info("Assembling final video with per-segment narration")
            
            # Filter out None images
            valid_images = [img for img in scene_images if img and Path(img).exists()]
            
            if not valid_images:
                logger.error("No valid scene images provided")
                return None
            
            # Ensure script_segments match valid_images count
            if len(script_segments) != len(valid_images):
                logger.warning(f"Segment count mismatch: {len(script_segments)} segments vs {len(valid_images)} images")
                # Adjust to minimum length
                min_length = min(len(script_segments), len(valid_images))
                script_segments = script_segments[:min_length]
                valid_images = valid_images[:min_length]
            
            # Generate per-segment narration if enabled
            preferences = context.get("preferences", {})
            segment_audio_paths = []
            durations = []
            
            if preferences.get("narration", True):
                logger.info("Generating per-segment narration")
                audio_output_dir = get_temp_path("", "audio")
                
                for i, segment in enumerate(script_segments):
                    # Generate narration for this segment
                    narration_info = self.generate_segment_narration(
                        segment=segment,
                        segment_index=i,
                        output_dir=audio_output_dir
                    )
                    
                    if narration_info:
                        # Use actual audio duration
                        segment_audio_paths.append(narration_info["audio_path"])
                        durations.append(narration_info["duration"])
                        logger.info(f"Segment {i + 1}: {narration_info['duration']:.2f}s (from audio)")
                    else:
                        # No narration for this segment, use default duration
                        segment_audio_paths.append(None)
                        default_duration = segment.get("duration_seconds", 5.0)
                        durations.append(default_duration)
                        logger.info(f"Segment {i + 1}: {default_duration:.2f}s (default, no narration)")
            else:
                # No narration, use segment durations from script
                logger.info("Narration disabled, using script segment durations")
                for segment in script_segments:
                    segment_audio_paths.append(None)
                    durations.append(segment.get("duration_seconds", 5.0))
            
            # Log total duration
            total_duration = sum(durations)
            logger.info(f"Total video duration: {total_duration:.2f}s ({len(durations)} segments)")
            
            # Create video from images with per-segment audio
            logger.info("Creating video from scene images with per-segment audio")
            video_path = self.video_tool.create_video_from_images(
                image_paths=valid_images,
                durations=durations,
                segment_audio_paths=segment_audio_paths,
                fps=self.config.video.fps,
                transition_duration=self.config.video.transition_duration
            )
            
            if not video_path:
                logger.error("Failed to create video from images")
                return None
            
            # Get background music if enabled
            music_path = None
            if preferences.get("music", True) and self.config.video.background_music:
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
            
            # Create final video with background music and end card
            # Note: narration is already embedded in video_path from per-segment audio
            logger.info("Creating final video with background music and end card")
            final_video_path = self.video_tool.create_final_video(
                video_path=video_path,
                narration_audio=None,  # Already embedded in video
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

