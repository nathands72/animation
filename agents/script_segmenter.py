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
    
    scene_number: int = Field(description="Scene number (1-indexed) - REQUIRED")
    description: str = Field(description="Detailed scene description for visual generation - REQUIRED")
    characters: List[str] = Field(description="List of ALL character names mentioned in description, dialogue, or narration - REQUIRED (include every character, even if mentioned briefly)")
    dialogue: Optional[str] = Field(description="Optional character dialogue (null if no dialogue)", default=None)
    narration: str = Field(description="Narration text for this segment - REQUIRED (part of full story, never empty)")
    duration_seconds: float = Field(description="Scene duration in seconds (4-8 seconds) - REQUIRED")
    setting: str = Field(description="Brief setting description (1-2 words, e.g., 'forest', 'cave') - REQUIRED")
    scene_background: str = Field(description="Detailed scene background description (2-3 sentences including lighting, atmosphere, time of day, weather, environmental details, and visual mood for consistency) - REQUIRED")
    emotions: List[str] = Field(description="List of emotions to convey in this scene - REQUIRED (at least one emotion)")



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
            api_key=self.config.llm.api_key,
            base_url=self.config.llm.base_url
        )
        self.output_parser = PydanticOutputParser(pydantic_object=ScriptSegments)
        
        # System prompt for script segmentation
        self.system_prompt = """You are a script segmentation expert for animated video production.

⚠️ ABSOLUTE CRITICAL REQUIREMENT ⚠️
YOU MUST INCLUDE 100% OF THE STORY TEXT IN THE SEGMENT NARRATIONS.
DO NOT SKIP, SUMMARIZE, OR PARAPHRASE ANY PART OF THE STORY.
EVERY SINGLE SENTENCE FROM THE STORY MUST APPEAR IN EXACTLY ONE SEGMENT'S NARRATION FIELD.

Your role is to break a story into 8-20 visual scene segments where:
1. THE ENTIRE STORY TEXT (EVERY WORD, EVERY SENTENCE) MUST BE DISTRIBUTED ACROSS SEGMENT NARRATIONS
2. Each segment's narration should be a CONTINUOUS, VERBATIM portion of the original story
3. Narration should flow naturally from one segment to the next with NO GAPS OR MISSING TEXT
4. Each scene is 4-8 seconds long (adjust duration based on narration length)
5. Each scene has clear visual elements (characters, setting, actions)
6. Visual descriptions should match the narration content
7. Each scene includes character emotions and expressions
8. The total video duration matches the target (approximately 3-5 minutes)

CRITICAL STORY COVERAGE REQUIREMENTS (READ CAREFULLY):
❌ DO NOT summarize the story - copy the exact text
❌ DO NOT paraphrase sentences - use the original wording
❌ DO NOT skip paragraphs or sentences - include everything
❌ DO NOT stop before reaching the end - segment the ENTIRE story
✅ DO copy each sentence from the story exactly as written
✅ DO start with the very first word of the story
✅ DO end with the very last word of the story
✅ DO verify that concatenating all narrations = complete original story

VERIFICATION CHECKLIST BEFORE SUBMITTING:
1. Did I include the first sentence of the story in segment 1's narration? ✓
2. Did I include the last sentence of the story in the final segment's narration? ✓
3. Are there any sentences from the story that I skipped? (Answer must be NO)
4. Did I paraphrase or summarize any part? (Answer must be NO)
5. If I concatenate all segment narrations, does it equal the full story? (Answer must be YES)

REQUIRED FIELDS FOR EVERY SEGMENT (INCLUDING THE LAST ONE):
You MUST provide ALL of the following fields for EVERY segment without exception:
1. scene_number - Sequential number (1, 2, 3, etc.)
2. description - Detailed scene description for visual generation
3. characters - List of ALL character names mentioned in this segment (IMPORTANT: see below)
4. dialogue - Character dialogue (can be null/empty if no dialogue)
5. narration - VERBATIM text from the story (REQUIRED - never empty, never summarized)
6. duration_seconds - Scene duration (must be a number between 4-8)
7. setting - Brief setting description (1-2 words, e.g., "forest", "cave")
8. scene_background - Detailed 2-3 sentence description with lighting, atmosphere, time of day, weather, environmental details, and visual mood
9. emotions - List of emotions to convey (at least one emotion, e.g., ["joy"], ["tension", "fear"])

CRITICAL CHARACTER LISTING REQUIREMENTS:
The "characters" field MUST include ALL characters that appear in ANY of these fields for that segment:
- Characters mentioned in the description
- Characters speaking in the dialogue
- Characters mentioned in the narration
- Characters performing actions in the scene

Example: If the narration says "Leo found a feather and showed it to Mia", then characters MUST be ["Leo", "Mia"]
Example: If the dialogue is "'Look!' said Leo to Mia and Sam", then characters MUST be ["Leo", "Mia", "Sam"]
Example: If only the description mentions "Leo alone in the forest", then characters should be ["Leo"]

DO NOT omit characters even if they only appear briefly or are just mentioned in passing.
The characters list should be comprehensive and include every character name that appears in the segment.

CRITICAL: The LAST segment is just as important as the first. Do NOT omit any fields in the final segment.

IMPORTANT FOR VISUAL CONSISTENCY:
- Scene backgrounds should be detailed and specific to help maintain consistency across scenes
- If multiple scenes share the same location, use very similar background descriptions
- Include details like: lighting quality (soft morning light, golden sunset, moonlit night), weather (clear sky, misty, rainy), atmosphere (peaceful, tense, magical), and environmental specifics (dense trees, rocky terrain, cozy interior)

Ensure visual continuity between scenes (characters maintain consistent appearance)."""

        self.human_prompt = """Break the following story into 8-20 visual scene segments:

Story:
{story}

Context:
{context}

Target Duration: {duration_minutes} minutes

{format_instructions}

⚠️⚠️⚠️ CRITICAL INSTRUCTIONS - READ BEFORE STARTING ⚠️⚠️⚠️

YOUR PRIMARY GOAL: Include 100% of the story text in segment narrations.

STEP-BY-STEP PROCESS TO FOLLOW:
1. Read the ENTIRE story from beginning to end
2. Identify natural break points (scene changes, dialogue shifts, action changes)
3. Starting from the FIRST WORD of the story, copy text verbatim into segment 1's narration
4. Continue to the next break point, copy that text verbatim into segment 2's narration
5. Repeat until you reach the LAST WORD of the story
6. Verify: Does concatenating all narrations = the complete original story? If NO, you failed.

WHAT YOU MUST DO:
✅ Copy the story text EXACTLY as written (word-for-word, sentence-by-sentence)
✅ Start segment 1 with the very first sentence of the story
✅ End the final segment with the very last sentence of the story
✅ Include EVERY sentence between the first and last
✅ Create as many segments as needed (8-20) to cover the ENTIRE story
✅ Split only at natural narrative breaks

WHAT YOU MUST NOT DO:
❌ DO NOT write "The story continues..." or similar - include the actual text
❌ DO NOT summarize (e.g., "Leo goes on a journey" instead of the actual journey text)
❌ DO NOT paraphrase (e.g., changing "beautiful golden feather" to "pretty feather")
❌ DO NOT skip paragraphs because they seem less important
❌ DO NOT stop before reaching the end because you've hit a segment count
❌ DO NOT truncate the ending to fit a target duration

REQUIRED FIELDS - ALL 9 FIELDS MUST BE PRESENT IN EVERY SEGMENT:
Every segment MUST include all of these fields:
- scene_number (integer)
- description (string)
- characters (list of strings) - MUST include ALL characters mentioned in description, dialogue, OR narration
- dialogue (string or null)
- narration (string, VERBATIM from story, never empty, never summarized)
- duration_seconds (float, 4.0-8.0)
- setting (string, 1-2 words)
- scene_background (string, 2-3 detailed sentences)
- emotions (list of strings, at least one)

IMPORTANT - CHARACTER LISTING RULES:
When populating the "characters" field, you MUST:
1. Read the description, dialogue, and narration for that segment
2. Extract EVERY character name mentioned in ANY of those fields
3. Include all extracted names in the characters array
4. Do NOT omit characters even if they're only mentioned briefly

Examples of correct character listing:
- Narration: "Leo showed the feather to Mia" → characters: ["Leo", "Mia"]
- Dialogue: "'Hello!' said Sam to Leo and Mia" → characters: ["Sam", "Leo", "Mia"]  
- Description: "Leo, Mia, and the Golden Eagle meet" → characters: ["Leo", "Mia", "Golden Eagle"]
- Narration: "Leo thought about what Mia had said" → characters: ["Leo", "Mia"]

Examples of INCORRECT character listing (DO NOT DO THIS):
- Narration: "Leo showed the feather to Mia" → characters: ["Leo"] ❌ (Missing Mia!)
- Dialogue: "'Hello!' said Sam to Leo" → characters: ["Sam"] ❌ (Missing Leo!)

Example of a COMPLETE segment with ALL required fields:
{{
  "scene_number": 1,
  "description": "Leo discovers a golden feather in the magical forest",
  "characters": ["Leo", "Mia"],
  "dialogue": null,
  "narration": "Once upon a time, in a magical forest, lived Leo the lion. One day, he found a beautiful golden feather.",
  "duration_seconds": 6.0,
  "setting": "Magical forest",
  "scene_background": "A vibrant magical forest with towering ancient trees and glittering leaves. Soft golden sunlight filters through the dense canopy, creating dappled patterns on the mossy forest floor. The atmosphere is peaceful and enchanting with a slight morning mist.",
  "emotions": ["curiosity", "wonder"]
}}

SELF-CHECK BEFORE SUBMITTING YOUR RESPONSE:
□ Does segment 1's narration start with the first sentence of the story?
□ Does the final segment's narration end with the last sentence of the story?
□ Did I include every sentence from the story without skipping any?
□ Did I copy the text exactly without paraphrasing or summarizing?
□ Does every segment have all 9 required fields?
□ If I concatenate all narrations, do I get the complete original story?

If you cannot answer YES to all of the above, DO NOT SUBMIT. Go back and fix it.

CRITICAL REMINDER: The LAST segment (segment 8-20) MUST have ALL 9 fields just like the first segment. Do not omit duration_seconds, setting, scene_background, or emotions from the final segment.

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
                    "scene_background": segment.scene_background,
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
            
            # Calculate character-level similarity to detect paraphrasing
            story_chars = len(original_story)
            narration_chars = len(combined_narration)
            char_ratio = narration_chars / story_chars if story_chars > 0 else 0
            
            # Log detailed coverage information
            logger.info(f"Story coverage: {coverage:.1%} ({len(narration_words)} words in narration vs {len(story_words)} in story)")
            logger.info(f"Character count: {narration_chars} in narration vs {story_chars} in story (ratio: {char_ratio:.1%})")
            logger.info(f"Number of segments: {len(segments)}")
            
            # Show first and last narration snippets for debugging
            if segments:
                first_narration = segments[0].get("narration", "")[:100]
                last_narration = segments[-1].get("narration", "")[-100:]  # Last 100 chars
                first_story = original_story[:100]
                last_story = original_story[-100:]
                
                logger.info(f"First segment narration: {first_narration}...")
                logger.info(f"First story text:        {first_story}...")
                logger.info(f"Last segment narration:  ...{last_narration}")
                logger.info(f"Last story text:         ...{last_story}")
            
            # Require at least 85% word coverage
            if coverage < 0.85:
                logger.warning(f"Story coverage only {coverage:.1%}, below 85% threshold")
                logger.warning("LLM may have truncated or summarized the story instead of using exact text")
                logger.warning(f"Missing {len(story_words - narration_words)} unique words from original story")
                return False
            
            # Check that combined narration is substantial (should be close to original length)
            if char_ratio < 0.75:
                logger.warning(f"Combined narration too short: {narration_chars} chars vs {story_chars} story chars (ratio: {char_ratio:.1%})")
                logger.warning("LLM likely summarized instead of copying verbatim")
                return False
            
            logger.info(f"✓ Story coverage validation passed: {coverage:.1%} word coverage, {char_ratio:.1%} character ratio")
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
            # Create a basic scene background from setting
            scene_background = f"{setting}. The scene has a neutral atmosphere with natural lighting. A calm and peaceful environment."
            
            segments.append({
                "scene_number": i,
                "description": paragraph[:200],  # First 200 chars
                "characters": characters[:2] if characters else [],  # First 2 characters
                "dialogue": None,
                "narration": paragraph,
                "duration_seconds": duration_per_segment,
                "setting": setting,
                "scene_background": scene_background,
                "emotions": ["neutral"],
            })
        
        return segments

