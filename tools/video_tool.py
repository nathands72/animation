"""Video processing tool with MoviePy integration."""

import logging
import os
from pathlib import Path
from typing import List, Optional, Dict, Any
import tempfile

from config import get_config
from utils.helpers import get_temp_path, get_output_path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

# Configure ImageMagick path for MoviePy TextClip
# This is required for text overlays and end cards
try:
    from moviepy.config import change_settings
    
    # Try to find ImageMagick binary
    imagemagick_binary = os.getenv("IMAGEMAGICK_BINARY")
    
    if not imagemagick_binary:
        # Common ImageMagick installation paths on Windows
        possible_paths = [
            r"C:\Program Files\ImageMagick-7.1.1-Q16\magick.exe",
            r"C:\Program Files\ImageMagick-7.1.0-Q16\magick.exe",
            r"C:\Program Files\ImageMagick-7.0.0-Q16\magick.exe",
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                imagemagick_binary = path
                break
    
    if imagemagick_binary and os.path.exists(imagemagick_binary):
        change_settings({"IMAGEMAGICK_BINARY": imagemagick_binary})
        logger.info(f"ImageMagick configured: {imagemagick_binary}")
    else:
        logger.warning("ImageMagick not found. Text overlays will not work. Install from: https://imagemagick.org")
except Exception as e:
    logger.warning(f"Could not configure ImageMagick: {e}")



class VideoProcessingTool:
    """Video processing tool with MoviePy."""
    
    def __init__(self):
        """Initialize video processing tool."""
        self.config = get_config()
        try:
            from moviepy.editor import VideoFileClip, ImageClip, CompositeVideoClip, concatenate_videoclips, concatenate_audioclips, AudioFileClip, TextClip
            from moviepy.video.fx.fadein import fadein
            from moviepy.video.fx.fadeout import fadeout
            self.moviepy = True
            self.VideoFileClip = VideoFileClip
            self.ImageClip = ImageClip
            self.CompositeVideoClip = CompositeVideoClip
            self.concatenate_videoclips = concatenate_videoclips
            self.concatenate_audioclips = concatenate_audioclips
            self.AudioFileClip = AudioFileClip
            self.TextClip = TextClip
            self.fadein = fadein
            self.fadeout = fadeout
            logger.info("MoviePy initialized")
        except ImportError:
            logger.error("MoviePy not installed")
            self.moviepy = False
    
    def create_video_from_images(
        self,
        image_paths: List[Path],
        durations: Optional[List[float]] = None,
        segment_audio_paths: Optional[List[Optional[Path]]] = None,
        output_path: Optional[Path] = None,
        fps: Optional[int] = None,
        transition_duration: Optional[float] = None
    ) -> Optional[Path]:
        """
        Create video from sequence of images.
        
        Args:
            image_paths: List of paths to image files
            durations: Optional list of durations for each image (default: 5 seconds)
            segment_audio_paths: Optional list of audio paths for each segment
            output_path: Optional output path (auto-generated if not provided)
            fps: Optional FPS (default from config)
            transition_duration: Optional transition duration (default from config)
            
        Returns:
            Path to generated video file, or None if creation failed
        """
        if not self.moviepy:
            logger.error("MoviePy not available")
            return None
        
        if not image_paths:
            logger.error("No images provided")
            return None
        
        if fps is None:
            fps = self.config.video.fps
        
        if transition_duration is None:
            transition_duration = self.config.video.transition_duration
        
        if durations is None:
            # Default duration: 5 seconds per image
            durations = [5.0] * len(image_paths)
        
        if len(durations) != len(image_paths):
            logger.warning("Durations list length doesn't match images, using default")
            durations = [5.0] * len(image_paths)
        
        try:
            logger.info(f"Creating video from {len(image_paths)} images")
            
            # Ensure segment_audio_paths matches image_paths length
            if segment_audio_paths is None:
                segment_audio_paths = [None] * len(image_paths)
            elif len(segment_audio_paths) < len(image_paths):
                # Pad with None if needed
                segment_audio_paths = segment_audio_paths + [None] * (len(image_paths) - len(segment_audio_paths))
            
            # Create clips from images
            clips = []
            for i, (image_path, duration) in enumerate(zip(image_paths, durations)):
                if not image_path.exists():
                    logger.warning(f"Image not found: {image_path}, skipping")
                    continue
                
                clip = self.ImageClip(str(image_path), duration=duration)
                
                # Add per-segment audio if provided
                if i < len(segment_audio_paths) and segment_audio_paths[i]:
                    audio_path = segment_audio_paths[i]
                    if audio_path.exists():
                        try:
                            audio_clip = self.AudioFileClip(str(audio_path))
                            clip = clip.set_audio(audio_clip)
                            logger.info(f"Attached audio to segment {i + 1}: {audio_path.name}")
                        except Exception as e:
                            logger.warning(f"Failed to attach audio to segment {i + 1}: {e}")
                
                # Add fade transitions
                if i > 0:  # Fade in (except first clip)
                    clip = clip.fx(self.fadein, transition_duration)
                if i < len(image_paths) - 1:  # Fade out (except last clip)
                    clip = clip.fx(self.fadeout, transition_duration)
                
                clips.append(clip)
            
            if not clips:
                logger.error("No valid clips created")
                return None
            
            # Concatenate clips
            final_clip = self.concatenate_videoclips(clips, method="compose")
            
            # Set FPS
            final_clip = final_clip.set_fps(fps)
            
            # Determine output path
            if output_path is None:
                output_path = get_temp_path("video_segment.mp4", "video")
            
            # Write video
            logger.info(f"Writing video to: {output_path}")
            final_clip.write_videofile(
                str(output_path),
                fps=fps,
                codec='libx264',
                audio_codec='aac',
                preset='medium',
                logger=None  # Suppress MoviePy logging
            )
            
            # Close clips to free memory
            final_clip.close()
            for clip in clips:
                clip.close()
            
            logger.info(f"Video created successfully: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error creating video: {e}")
            return None
    
    def add_audio_to_video(
        self,
        video_path: Path,
        audio_path: Path,
        output_path: Optional[Path] = None,
        audio_volume: Optional[float] = None
    ) -> Optional[Path]:
        """
        Add audio track to video.
        
        Args:
            video_path: Path to video file
            audio_path: Path to audio file
            output_path: Optional output path
            audio_volume: Optional audio volume (0.0 to 1.0)
            
        Returns:
            Path to video with audio, or None if failed
        """
        if not self.moviepy:
            logger.error("MoviePy not available")
            return None
        
        if not video_path.exists():
            logger.error(f"Video not found: {video_path}")
            return None
        
        if not audio_path.exists():
            logger.error(f"Audio not found: {audio_path}")
            return None
        
        try:
            logger.info(f"Adding audio to video: {audio_path}")
            
            # Load video and audio
            video = self.VideoFileClip(str(video_path))
            audio = self.AudioFileClip(str(audio_path))
            
            # Adjust audio volume
            if audio_volume is not None:
                audio = audio.volumex(audio_volume)
            
            # Set audio duration to match video
            if audio.duration > video.duration:
                audio = audio.subclip(0, video.duration)
            elif audio.duration < video.duration:
                # Loop audio if shorter than video
                loops_needed = int(video.duration / audio.duration) + 1
                audio = self.concatenate_audioclips([audio] * loops_needed)
                audio = audio.subclip(0, video.duration)
            
            # Combine video and audio
            final_video = video.set_audio(audio)
            
            # Determine output path
            if output_path is None:
                output_path = get_temp_path("video_with_audio.mp4")
            
            # Write video
            final_video.write_videofile(
                str(output_path),
                codec='libx264',
                audio_codec='aac',
                preset='medium',
                logger=None
            )
            
            # Close clips
            final_video.close()
            video.close()
            audio.close()
            
            logger.info(f"Video with audio created: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error adding audio to video: {e}")
            return None
    
    def add_text_overlay(
        self,
        video_path: Path,
        text: str,
        position: str = "bottom",
        duration: Optional[float] = None,
        output_path: Optional[Path] = None
    ) -> Optional[Path]:
        """
        Add text overlay to video.
        
        Args:
            video_path: Path to video file
            text: Text to overlay
            position: Text position ("top", "center", "bottom")
            duration: Optional text duration (default: full video)
            output_path: Optional output path
            
        Returns:
            Path to video with text overlay, or None if failed
        """
        if not self.moviepy:
            logger.error("MoviePy not available")
            return None
        
        try:
            logger.info(f"Adding text overlay: {text[:50]}...")
            
            # Load video
            video = self.VideoFileClip(str(video_path))
            
            # Create text clip
            text_clip = self.TextClip(
                text,
                fontsize=40,
                color='white',
                font='Arial-Bold',
                stroke_color='black',
                stroke_width=2
            )
            
            # Set text duration
            if duration is None:
                duration = video.duration
            text_clip = text_clip.set_duration(duration)
            
            # Set text position
            if position == "top":
                text_clip = text_clip.set_position(('center', 'top')).set_margin(20)
            elif position == "center":
                text_clip = text_clip.set_position('center')
            else:  # bottom
                text_clip = text_clip.set_position(('center', 'bottom')).set_margin(20)
            
            # Composite video and text
            final_video = self.CompositeVideoClip([video, text_clip])
            
            # Determine output path
            if output_path is None:
                output_path = get_temp_path("video_with_text.mp4")
            
            # Write video
            final_video.write_videofile(
                str(output_path),
                codec='libx264',
                audio_codec='aac',
                preset='medium',
                logger=None
            )
            
            # Close clips
            final_video.close()
            video.close()
            text_clip.close()
            
            logger.info(f"Video with text overlay created: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error adding text overlay: {e}")
            return None
    
    def create_final_video(
        self,
        video_path: Path,
        narration_audio: Optional[Path] = None,
        background_music: Optional[Path] = None,
        moral_message: Optional[str] = None,
        output_path: Optional[Path] = None
    ) -> Optional[Path]:
        """
        Create final video with narration, music, and end card.
        
        Args:
            video_path: Path to main video file
            narration_audio: Optional path to narration audio
            background_music: Optional path to background music
            moral_message: Optional moral message for end card
            output_path: Optional output path
            
        Returns:
            Path to final video, or None if failed
        """
        if not self.moviepy:
            logger.error("MoviePy not available")
            return None
        
        try:
            logger.info("Creating final video")
            
            # Load main video
            video = self.VideoFileClip(str(video_path))
            
            # Add narration if provided
            if narration_audio and narration_audio.exists():
                logger.info("Adding narration audio")
                narration = self.AudioFileClip(str(narration_audio))
                
                # Set narration duration to match video
                if narration.duration > video.duration:
                    narration = narration.subclip(0, video.duration)
                
                # Set narration volume (higher than background music)
                narration = narration.volumex(0.8)
                
                # Add background music if provided
                if background_music and background_music.exists():
                    logger.info("Adding background music")
                    music = self.AudioFileClip(str(background_music))
                    
                    # Set music volume (lower than narration)
                    music = music.volumex(self.config.video.music_volume)
                    
                    # Set music duration to match video
                    if music.duration > video.duration:
                        music = music.subclip(0, video.duration)
                    elif music.duration < video.duration:
                        # Loop music if shorter
                        loops_needed = int(video.duration / music.duration) + 1
                        music = self.concatenate_audioclips([music] * loops_needed)
                        music = music.subclip(0, video.duration)
                    
                    # Composite audio (narration + music)
                    from moviepy.audio.AudioClip import CompositeAudioClip
                    composite_audio = CompositeAudioClip([narration, music])
                    video = video.set_audio(composite_audio)
                else:
                    video = video.set_audio(narration)
            
            # Add end card with moral message if provided
            if moral_message:
                try:
                    logger.info("Adding end card with moral message")
                    
                    # Create end card (3 seconds)
                    end_card_duration = 3.0
                    end_card = self.TextClip(
                        moral_message,
                        fontsize=50,
                        color='white',
                        font='Arial-Bold',
                        stroke_color='black',
                        stroke_width=3,
                        size=(video.w, video.h),
                        method='caption'
                    ).set_duration(end_card_duration).set_position('center')
                    
                    # Add fade in/out to end card
                    end_card = end_card.fx(self.fadein, 0.5).fx(self.fadeout, 0.5)
                    
                    # Concatenate video and end card
                    video = self.concatenate_videoclips([video, end_card], method="compose")
                    logger.info("End card added successfully")
                except Exception as e:
                    logger.warning(f"Could not add end card (ImageMagick may not be installed): {e}")
                    logger.warning("Continuing without end card. To add end cards, install ImageMagick from: https://imagemagick.org")
            
            # Determine output path
            if output_path is None:
                output_path = get_output_path("final_video.mp4")
            
            # Set resolution
            resolution = self.config.video.output_resolution
            if resolution == "720p":
                video = video.resize((1280, 720))
            elif resolution == "1080p":
                video = video.resize((1920, 1080))
            
            # Write final video
            logger.info(f"Writing final video to: {output_path}")
            video.write_videofile(
                str(output_path),
                fps=self.config.video.fps,
                codec='libx264',
                audio_codec='aac',
                preset='medium',
                logger=None
            )
            
            # Close clips
            video.close()
            
            logger.info(f"Final video created: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error creating final video: {e}")
            return None

