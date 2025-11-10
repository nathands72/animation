"""Story Generation Agent for creating engaging moral stories."""

import logging
from typing import Dict, Any, Optional

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate

from config import get_config
from utils.validators import validate_story_quality, validate_age_appropriateness

logger = logging.getLogger(__name__)


class StoryGeneratorAgent:
    """Agent for generating age-appropriate moral stories."""
    
    def __init__(self):
        """Initialize story generator agent."""
        self.config = get_config()
        self.llm = ChatOpenAI(
            model_name=self.config.llm.model,
            temperature=self.config.llm.temperature,
            max_tokens=self.config.llm.max_tokens,
            api_key=self.config.llm.api_key
        )
        
        # System prompt for story generation
        self.system_prompt = """You are a children's story writer specializing in moral stories.

Your role is to create engaging, age-appropriate moral stories that:
1. Naturally incorporate the specified moral lesson
2. Feature the specified characters with distinct personalities
3. Take place in the specified setting
4. Are appropriate for the target age group
5. Have a clear structure: beginning, conflict, resolution
6. Are 3-5 minutes when read aloud (approximately 400-800 words)
7. Are child-safe and wholesome

Story Structure:
- Beginning: Introduce characters and setting
- Conflict: Present a challenge or problem related to the moral lesson
- Resolution: Show how the moral lesson helps resolve the conflict
- Conclusion: Reinforce the moral lesson

Ensure the story is:
- Age-appropriate in language and complexity
- Engaging and entertaining
- Clear in its moral message
- Safe for children (no violence, scary content, or inappropriate themes)

Write a complete, engaging moral story."""

        self.human_prompt = """Create a moral story based on the following context:

Context:
{context}

Research Summary:
{research_summary}

Generate a complete, engaging moral story that:
- Incorporates all specified characters with distinct personalities
- Takes place in the specified setting
- Naturally weaves in the moral lesson: {moral_lesson}
- Is appropriate for age group: {age_group}
- Is approximately 400-800 words (3-5 minutes when read aloud)
- Has a clear beginning, conflict, and resolution

Write the story now:"""

    def generate(
        self,
        context: Dict[str, Any],
        research_summary: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate a moral story.
        
        Args:
            context: Validated context with theme, characters, setting, moral lesson, age group
            research_summary: Optional research summary from web research
            
        Returns:
            Dictionary with generated story and metadata
        """
        try:
            logger.info("Generating moral story")
            
            # Format context for prompt
            context_text = self._format_context(context)
            
            # Use research summary if available
            if not research_summary:
                research_summary = "No additional research information available."
            
            # Create prompt
            prompt = ChatPromptTemplate.from_messages([
                SystemMessagePromptTemplate.from_template(self.system_prompt),
                HumanMessagePromptTemplate.from_template(self.human_prompt)
            ])
            
            formatted_prompt = prompt.format_messages(
                context=context_text,
                research_summary=research_summary,
                moral_lesson=context.get("moral_lesson", ""),
                age_group=context.get("age_group", "6-8")
            )
            
            # Call LLM
            response = self.llm.invoke(formatted_prompt)
            story = response.content.strip()
            
            # Validate story quality
            is_valid, error_message = validate_story_quality(story, context)
            if not is_valid:
                logger.warning(f"Story validation warning: {error_message}")
                # Continue anyway, but log warning
            
            # Check age appropriateness
            age_group = context.get("age_group", "6-8")
            is_appropriate, warning = validate_age_appropriateness(story, age_group)
            if not is_appropriate:
                logger.warning(f"Age appropriateness warning: {warning}")
            
            # Generate metadata
            metadata = self._generate_metadata(story, context)
            
            logger.info(f"Story generated successfully ({len(story)} characters)")
            
            return {
                "story": story,
                "metadata": metadata
            }
            
        except Exception as e:
            logger.error(f"Error generating story: {e}")
            raise
    
    def _format_context(self, context: Dict[str, Any]) -> str:
        """
        Format context for prompt.
        
        Args:
            context: Context dictionary
            
        Returns:
            Formatted context string
        """
        parts = []
        
        parts.append(f"Theme: {context.get('theme', 'N/A')}")
        parts.append(f"Setting: {context.get('setting', 'N/A')}")
        parts.append(f"Moral Lesson: {context.get('moral_lesson', 'N/A')}")
        parts.append(f"Age Group: {context.get('age_group', '6-8')}")
        parts.append(f"Target Duration: {context.get('duration_minutes', 3)} minutes")
        
        # Format characters
        characters = context.get("characters", [])
        if characters:
            parts.append("\nCharacters:")
            for char in characters:
                name = char.get("name", "Unknown")
                char_type = char.get("type", "unknown")
                traits = char.get("traits", [])
                traits_str = ", ".join(traits) if traits else "none specified"
                parts.append(f"  - {name} ({char_type}): {traits_str}")
        
        return "\n".join(parts)
    
    def _generate_metadata(self, story: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate story metadata.
        
        Args:
            story: Generated story text
            context: Context dictionary
            
        Returns:
            Dictionary with story metadata
        """
        word_count = len(story.split())
        char_count = len(story)
        
        # Estimate reading time (average 200 words per minute)
        estimated_reading_time = word_count / 200.0
        
        # Count character mentions
        characters = context.get("characters", [])
        character_mentions = {}
        for char in characters:
            name = char.get("name", "")
            if name:
                character_mentions[name] = story.lower().count(name.lower())
        
        return {
            "word_count": word_count,
            "character_count": char_count,
            "estimated_reading_time_minutes": estimated_reading_time,
            "character_mentions": character_mentions,
            "theme": context.get("theme", ""),
            "age_group": context.get("age_group", ""),
            "moral_lesson": context.get("moral_lesson", ""),
        }

