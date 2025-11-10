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
    dialogue: Optional[str] = Field(description="Dialogue text if any", default=None)
    narration: Optional[str] = Field(description="Narration text if any", default=None)
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

Your role is to break a story into 8-12 visual scene segments that:
1. Each scene is 4-8 seconds long
2. Each scene has clear visual elements (characters, setting, actions)
3. Scenes flow naturally with visual continuity
4. Each scene includes character emotions and expressions
5. Dialogue and narration are appropriately distributed
6. The total video duration matches the target (approximately 3-5 minutes)

For each scene, provide:
- Detailed visual description for image generation
- Character names present in the scene
- Dialogue or narration text (if applicable)
- Scene duration (4-8 seconds)
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

Create scene segments that can be visually represented in an animated video.
Each scene should be 4-8 seconds long, with clear visual descriptions."""

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

