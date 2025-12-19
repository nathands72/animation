"""Script Segmentation Agent for breaking story into visual scenes."""

import logging
import json
from typing import Dict, Any, List, Optional

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

from config import get_config

logger = logging.getLogger(__name__)


class SceneSegment(BaseModel):
    """Scene segment structure."""
    
    scene_number: int = Field(description="Scene number (1-indexed)")
    description: str = Field(description="Detailed scene description for visual generation")
    characters: List[str] = Field(description="List of character names in this scene")
    dialogue: Optional[str] = Field(description="Optional character dialogue", default=None)
    narration: str = Field(description="Narration text for this segment (required, part of full story)")
    duration_seconds: float = Field(description="Scene duration in seconds (4-8 seconds)")
    setting: str = Field(description="Setting description for this scene")
    emotions: List[str] = Field(description="List of emotions to convey in this scene")


class ScriptSegments(BaseModel):
    """Script segments structure."""
    
    segments: List[SceneSegment] = Field(description="List of scene segments")


class ScriptSegmentationAgent:
    """Agent for breaking story into visual scene segments."""
    
    def __init__(self):
        """Initialize script segmentation agent."""
        self.config = get_config()
        self.llm = ChatOpenAI(
            model_name=self.config.llm.model,
            temperature=self.config.llm.temperature,
            max_tokens=self.config.llm.max_tokens,
            api_key=self.config.llm.api_key
        )
        self.output_parser = PydanticOutputParser(pydantic_object=ScriptSegments)
        
        # System prompt for script segmentation
        self.system_prompt = """You are a script segmentation expert for animated video production.

Your role is to break a story into 8-12 visual scene segments where:
1. THE ENTIRE STORY TEXT MUST BE DISTRIBUTED ACROSS SEGMENT NARRATIONS
2. Each segment's narration should be a continuous portion of the original story
3. Narration should flow naturally from one segment to the next without gaps
4. Each scene is 4-8 seconds long (adjust duration based on narration length)
5. Each scene has clear visual elements (characters, setting, actions)
6. Visual descriptions should match the narration content
7. Each scene includes character emotions and expressions
8. The total video duration matches the target (approximately 3-5 minutes)

CRITICAL REQUIREMENTS:
- Every sentence of the story MUST appear in exactly one segment's narration field
- The concatenation of all segment narrations should equal the complete story
- Do not skip, summarize, or paraphrase the story - use the exact text
- Split the story at natural narrative breaks (scene changes, dialogue shifts)
- START from the very first sentence and END with the very last sentence
- Do NOT stop segmenting until you reach the end of the story

For each scene, provide:
- Detailed visual description for image generation
- Character names present in the scene
- Narration text (REQUIRED - a continuous portion of the original story)
- Optional dialogue if characters are speaking
- Scene duration (4-8 seconds, adjusted for narration length)
- Setting description
- Emotions to convey

Ensure visual continuity between scenes (characters maintain consistent appearance)."""

        self.human_prompt = """Break the following story into 8-12 visual scene segments:

Story:
{story}

Context:
{context}

Target Duration: {duration_minutes} minutes

{format_instructions}

IMPORTANT INSTRUCTIONS:
1. You MUST include the ENTIRE story from the first sentence to the last sentence
2. Each segment's narration field should contain consecutive sentences from the story
3. Do NOT skip any sentences or paragraphs
4. Do NOT summarize or paraphrase - use the exact story text
5. The narration fields of all segments, when concatenated, should equal the complete story
6. Start with segment 1 containing the beginning of the story
7. End with the final segment containing the end of the story
8. Create 8-12 segments total, distributing the story evenly

Example of correct segmentation:
If story is: "Sentence A. Sentence B. Sentence C. Sentence D."
Segment 1 narration: "Sentence A. Sentence B."
Segment 2 narration: "Sentence C. Sentence D."
(All sentences included, none skipped)

Now segment the story above following these requirements."""

    def segment(
        self,
        story: str,
        context: Dict[str, Any],
        target_duration_minutes: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Break story into visual scene segments.
        
        Args:
            story: Generated story text
            context: Context dictionary with characters, setting, etc.
            target_duration_minutes: Target video duration in minutes
            
        Returns:
            List of scene segment dictionaries
        """
        try:
            logger.info("Segmenting story into visual scenes")
            
            if target_duration_minutes is None:
                target_duration_minutes = context.get("duration_minutes", 3)
            
            # Format context for prompt
            context_text = self._format_context(context)
            
            # Create prompt
            prompt = ChatPromptTemplate.from_messages([
                SystemMessagePromptTemplate.from_template(self.system_prompt),
                HumanMessagePromptTemplate.from_template(self.human_prompt)
            ])
            
            formatted_prompt = prompt.format_messages(
                story=story,
                context=context_text,
                duration_minutes=target_duration_minutes,
                format_instructions=self.output_parser.get_format_instructions()
            )
            
            # Call LLM
            response = self.llm.invoke(formatted_prompt)
            
            # Parse response
            parsed = self.output_parser.parse(response.content)
            
            # Convert to list of dictionaries
            segments = []
            for segment in parsed.segments:
                segments.append({
                    "scene_number": segment.scene_number,
                    "description": segment.description,
                    "characters": segment.characters,
                    "dialogue": segment.dialogue,
                    "narration": segment.narration,
                    "duration_seconds": segment.duration_seconds,
                    "setting": segment.setting,
                    "emotions": segment.emotions,
                })
            
            # Validate story coverage
            if not self._validate_story_coverage(segments, story):
                logger.warning("Story coverage validation failed, attempting fallback")
                # Try fallback segmentation if validation fails
                segments = self._fallback_segmentation(story, context, target_duration_minutes)
            
            # Validate and adjust durations
            segments = self._validate_durations(segments, target_duration_minutes)
            
            logger.info(f"Story segmented into {len(segments)} scenes")
            
            return segments
            
        except Exception as e:
            logger.error(f"Error segmenting story: {e}")
            # Fallback: simple segmentation
            logger.warning("Falling back to simple segmentation")
            return self._fallback_segmentation(story, context, target_duration_minutes)
    
    def _format_context(self, context: Dict[str, Any]) -> str:
        """
        Format context for prompt.
        
        Args:
            context: Context dictionary
            
        Returns:
            Formatted context string
        """
        parts = []
        
        # Characters
        characters = context.get("characters", [])
        if characters:
            parts.append("Characters:")
            for char in characters:
                name = char.get("name", "Unknown")
                char_type = char.get("type", "unknown")
                traits = char.get("traits", [])
                traits_str = ", ".join(traits) if traits else "none"
                parts.append(f"  - {name} ({char_type}): {traits_str}")
        
        # Setting
        setting = context.get("setting", "")
        if setting:
            parts.append(f"\nSetting: {setting}")
        
        return "\n".join(parts)
    
    def _validate_durations(
        self,
        segments: List[Dict[str, Any]],
        target_duration_minutes: int
    ) -> List[Dict[str, Any]]:
        """
        Validate and adjust scene durations to match target.
        
        Args:
            segments: List of scene segments
            target_duration_minutes: Target duration in minutes
            
        Returns:
            Adjusted segments
        """
        target_duration_seconds = target_duration_minutes * 60
        
        # Calculate total duration
        total_duration = sum(seg.get("duration_seconds", 5.0) for seg in segments)
        
        # If total is close to target, return as is
        if abs(total_duration - target_duration_seconds) < 10:
            return segments
        
        # Adjust durations proportionally
        scale_factor = target_duration_seconds / total_duration if total_duration > 0 else 1.0
        
        adjusted = []
        for seg in segments:
            new_duration = seg.get("duration_seconds", 5.0) * scale_factor
            # Clamp to 4-8 seconds
            new_duration = max(4.0, min(8.0, new_duration))
            seg["duration_seconds"] = new_duration
            adjusted.append(seg)
        
        return adjusted
    
    def _validate_story_coverage(
        self,
        segments: List[Dict[str, Any]],
        original_story: str
    ) -> bool:
        """
        Verify that segment narrations cover the full story.
        
        Args:
            segments: List of scene segments
            original_story: Original complete story text
            
        Returns:
            True if story coverage is adequate, False otherwise
        """
        try:
            # Concatenate all narrations
            combined_narration = " ".join(
                seg.get("narration", "") for seg in segments
            )
            
            if not combined_narration.strip():
                logger.warning("No narration found in segments")
                return False
            
            # Calculate word coverage (allow some flexibility for minor edits)
            story_words = set(original_story.lower().split())
            narration_words = set(combined_narration.lower().split())
            
            if len(story_words) == 0:
                return False
            
            coverage = len(story_words & narration_words) / len(story_words)
            
            # Log detailed coverage information
            logger.info(f"Story coverage: {coverage:.1%} ({len(narration_words)} words in narration vs {len(story_words)} in story)")
            logger.info(f"Number of segments: {len(segments)}")
            
            # Show first and last narration snippets for debugging
            if segments:
                first_narration = segments[0].get("narration", "")[:100]
                last_narration = segments[-1].get("narration", "")[:100]
                logger.info(f"First segment narration: {first_narration}...")
                logger.info(f"Last segment narration: {last_narration}...")
            
            # Require at least 85% word coverage
            if coverage < 0.85:
                logger.warning(f"Story coverage only {coverage:.1%}, below 85% threshold")
                logger.warning("LLM may have truncated or summarized the story instead of using exact text")
                return False
            
            # Check that combined narration is substantial
            if len(narration_words) < len(story_words) * 0.8:
                logger.warning(f"Combined narration too short: {len(narration_words)} vs {len(story_words)} story words")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating story coverage: {e}")
            return False
    
    def _fallback_segmentation(
        self,
        story: str,
        context: Dict[str, Any],
        target_duration_minutes: int
    ) -> List[Dict[str, Any]]:
        """
        Simple fallback segmentation without LLM.
        
        Args:
            story: Story text
            context: Context dictionary
            target_duration_minutes: Target duration
            
        Returns:
            List of basic scene segments
        """
        # Split story into paragraphs
        paragraphs = [p.strip() for p in story.split("\n\n") if p.strip()]
        
        # Create segments from paragraphs
        segments = []
        characters = [char.get("name", "") for char in context.get("characters", [])]
        setting = context.get("setting", "")
        
        num_segments = min(len(paragraphs), 10)  # Max 10 segments
        duration_per_segment = (target_duration_minutes * 60) / num_segments
        duration_per_segment = max(4.0, min(8.0, duration_per_segment))
        
        for i, paragraph in enumerate(paragraphs[:num_segments], 1):
            segments.append({
                "scene_number": i,
                "description": paragraph[:200],  # First 200 chars
                "characters": characters[:2] if characters else [],  # First 2 characters
                "dialogue": None,
                "narration": paragraph,
                "duration_seconds": duration_per_segment,
                "setting": setting,
                "emotions": ["neutral"],
            })
        
        return segments

