"""Validation functions for input and content quality."""

import re
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)


# Inappropriate words/phrases for child content (basic list - can be expanded)
INAPPROPRIATE_WORDS = [
    "violence", "weapon", "kill", "death", "blood", "horror", "scary",
    "frightening", "terrifying", "inappropriate", "adult", "mature"
]


def validate_input(input_data: Dict[str, Any]) -> tuple[bool, Optional[str]]:
    """
    Validate input context and preferences.
    
    Args:
        input_data: Input dictionary with 'context' and 'preferences' keys
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not isinstance(input_data, dict):
        return False, "Input must be a dictionary"
    
    if "context" not in input_data:
        return False, "Missing 'context' key in input"
    
    context = input_data["context"]
    
    # Validate required context fields
    required_fields = ["topic", "theme", "characters", "setting", "moral_lesson", "age_group"]
    for field in required_fields:
        if field not in context:
            return False, f"Missing required field in context: {field}"
    
    # Validate topic
    if not isinstance(context["topic"], str) or not context["topic"].strip():
        return False, "Topic must be a non-empty string"
    
    # Validate theme
    if not isinstance(context["theme"], str) or not context["theme"].strip():
        return False, "Theme must be a non-empty string"
    
    # Validate characters
    if not isinstance(context["characters"], list) or len(context["characters"]) == 0:
        return False, "Characters must be a non-empty list"
    
    for i, char in enumerate(context["characters"]):
        if not isinstance(char, dict):
            return False, f"Character {i} must be a dictionary"
        if "name" not in char or "type" not in char:
            return False, f"Character {i} must have 'name' and 'type' fields"
    
    # Validate setting
    if not isinstance(context["setting"], str) or not context["setting"].strip():
        return False, "Setting must be a non-empty string"
    
    # Validate moral_lesson
    if not isinstance(context["moral_lesson"], str) or not context["moral_lesson"].strip():
        return False, "Moral lesson must be a non-empty string"
    
    # Validate age_group
    """
    valid_age_groups = ["3-5", "6-8", "9-12"]
    if context["age_group"] not in valid_age_groups:
        return False, f"Age group must be one of: {', '.join(valid_age_groups)}"
    """
    # Validate duration if provided
    if "duration_minutes" in context:
        duration = context["duration_minutes"]
        if not isinstance(duration, int) or duration < 1 or duration > 10:
            return False, "Duration must be an integer between 1 and 10 minutes"
    
    # Validate preferences if provided
    if "preferences" in input_data:
        prefs = input_data["preferences"]
        if not isinstance(prefs, dict):
            return False, "Preferences must be a dictionary"
        
        """
        if "art_style" in prefs:
            valid_styles = ["cartoon", "watercolor", "3D", "2D"]
            if prefs["art_style"] not in valid_styles:
                return False, f"Art style must be one of: {', '.join(valid_styles)}"
        """
    return True, None


def validate_age_appropriateness(content: str, age_group: str) -> tuple[bool, Optional[str]]:
    """
    Check if content is age-appropriate.
    
    Args:
        content: Content to check (story, dialogue, etc.)
        age_group: Target age group ("3-5", "6-8", "9-12")
        
    Returns:
        Tuple of (is_appropriate, warning_message)
    """
    content_lower = content.lower()
    
    # Check for inappropriate words
    found_words = []
    for word in INAPPROPRIATE_WORDS:
        if word in content_lower:
            found_words.append(word)
    
    if found_words:
        return False, f"Content contains inappropriate words: {', '.join(found_words)}"
    
    # Check reading level based on age group
    if age_group == "3-5":
        # Very simple words, short sentences
        sentences = re.split(r'[.!?]+', content)
        avg_sentence_length = sum(len(s.split()) for s in sentences) / max(len(sentences), 1)
        if avg_sentence_length > 8:
            return False, "Content too complex for age group 3-5 (sentences too long)"
    
    # Check for complex vocabulary for younger groups
    if age_group in ["3-5", "6-8"]:
        complex_words = ["therefore", "however", "consequently", "nevertheless"]
        found_complex = [w for w in complex_words if w in content_lower]
        if found_complex:
            logger.warning(f"Complex words found for age group {age_group}: {found_complex}")
    
    return True, None


def validate_story_quality(story: str, context: Dict[str, Any]) -> tuple[bool, Optional[str]]:
    """
    Validate story quality and completeness.
    
    Args:
        story: Generated story text
        context: Original context with theme, moral lesson, etc.
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not story or len(story.strip()) < 200:
        return False, "Story is too short (minimum 200 characters)"
    
    if len(story) > 5000:
        return False, "Story is too long (maximum 5000 characters)"
    
    # Check for story structure (beginning, middle, end indicators)
    story_lower = story.lower()
    
    # Check if moral lesson is mentioned
    moral_lesson = context.get("moral_lesson", "").lower()
    if moral_lesson and moral_lesson not in story_lower:
        # Check if key words from moral lesson appear
        moral_words = moral_lesson.split()
        found_words = sum(1 for word in moral_words if word in story_lower)
        if found_words < len(moral_words) * 0.3:  # At least 30% of words should appear
            logger.warning("Moral lesson may not be well integrated into story")
    
    # Check for character names
    characters = context.get("characters", [])
    if characters:
        character_names = [char.get("name", "").lower() for char in characters]
        found_characters = sum(1 for name in character_names if name in story_lower)
        if found_characters == 0:
            return False, "Story does not mention any of the specified characters"
    
    # Check for setting
    setting = context.get("setting", "").lower()
    if setting and setting not in story_lower:
        # Check if key words from setting appear
        setting_words = setting.split()
        found_words = sum(1 for word in setting_words if word in story_lower)
        if found_words < len(setting_words) * 0.5:
            logger.warning("Setting may not be well described in story")
    
    # Check age appropriateness
    age_group = context.get("age_group", "6-8")
    is_appropriate, warning = validate_age_appropriateness(story, age_group)
    if not is_appropriate:
        return False, warning
    
    return True, None


def validate_image_quality(image_path: str) -> tuple[bool, Optional[str]]:
    """
    Validate image quality and format.
    
    Args:
        image_path: Path to image file
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        from PIL import Image
        
        with Image.open(image_path) as img:
            width, height = img.size
            
            # Check minimum resolution
            if width < 1920 or height < 1080:
                return False, f"Image resolution too low: {width}x{height} (minimum 1920x1080)"
            
            # Check format
            if img.format not in ["PNG", "JPEG", "JPG"]:
                return False, f"Unsupported image format: {img.format}"
            
            # Check if image is readable
            img.verify()
            
    except Exception as e:
        return False, f"Error validating image: {str(e)}"
    
    return True, None


def validate_video_quality(video_path: str) -> tuple[bool, Optional[str]]:
    """
    Validate video quality and format.
    
    Args:
        video_path: Path to video file
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        from moviepy.editor import VideoFileClip
        
        with VideoFileClip(video_path) as video:
            duration = video.duration
            
            if duration < 1.0:
                return False, "Video duration too short (minimum 1 second)"
            
            if duration > 600:  # 10 minutes
                return False, "Video duration too long (maximum 10 minutes)"
            
            width, height = video.size
            if width < 720 or height < 480:
                return False, f"Video resolution too low: {width}x{height}"
            
    except Exception as e:
        return False, f"Error validating video: {str(e)}"
    
    return True, None

