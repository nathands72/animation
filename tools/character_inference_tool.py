"""Character inference tool for analyzing story segments and inferring character details."""

import logging
import json
import re
from typing import Dict, Any, List, Optional

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from config import get_config

logger = logging.getLogger(__name__)


class CharacterInferenceTool:
    """Tool for inferring character details from story segments using LLM."""
    
    def __init__(self):
        """Initialize character inference tool."""
        self.config = get_config()
        self.llm = ChatOpenAI(
            model_name=self.config.llm.model,
            temperature=0.3,  # Lower temperature for more consistent inference
            api_key=self.config.llm.api_key,
            base_url=self.config.llm.base_url
        )
        
        # System prompt for character inference
        self.inference_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a character analysis expert for children's stories. Your task is to analyze story segments and determine each character's type and personality traits.

For each character mentioned, you must infer:
1. Character type: What kind of creature or being they are (e.g., lion, owl, monkey, phoenix, dragon, rabbit, fox, human child, wizard, etc.)
2. Personality traits: 2-3 traits based on their dialogue, actions, and how they're described (e.g., brave, wise, mischievous, kind, cunning, etc.)

CRITICAL: You must respond with ONLY a valid JSON object. Do not include markdown code blocks, explanations, or any other text.

The JSON must use the ACTUAL character names from the story as keys."""),
            ("human", """Analyze these characters and infer their type and traits:

{character_info}

Story Context:
- Theme: {theme}
- Setting: {setting}
- Moral Lesson: {moral_lesson}

Return a JSON object where each key is a character name and the value contains "type" and "traits":
Example format (use ACTUAL character names, not these placeholders):
{{"Max": {{"type": "monkey", "traits": ["mischievous", "clever"]}}, "Phoenix": {{"type": "phoenix", "traits": ["wise", "magical"]}}}}""")
        ])
    
    def infer_characters_from_segments(
        self,
        character_names: List[str],
        script_segments: List[Dict[str, Any]],
        story_context: Dict[str, Any]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Infer character details from story segments.
        
        Args:
            character_names: List of character names to infer details for
            script_segments: List of script segments containing character appearances
            story_context: Story context with theme, setting, moral lesson
            
        Returns:
            Dictionary mapping character names to inferred details (type, traits)
        """
        try:
            logger.info(f"Inferring details for {len(character_names)} characters from story segments")
            
            # Gather context about each character from script segments
            character_contexts = self._gather_character_contexts(
                character_names, 
                script_segments
            )
            
            # Format character information for LLM
            char_info_parts = []
            for char_name, context in character_contexts.items():
                char_info_parts.append(f"**{char_name}**:")
                if context["descriptions"]:
                    char_info_parts.append(f"  Descriptions: {' | '.join(context['descriptions'][:3])}")
                if context["dialogues"]:
                    char_info_parts.append(f"  Dialogues: {' | '.join(context['dialogues'][:3])}")
            
            # Format prompt
            formatted_prompt = self.inference_prompt.format_messages(
                character_info="\n".join(char_info_parts),
                theme=story_context.get("theme", "N/A"),
                setting=story_context.get("setting", "N/A"),
                moral_lesson=story_context.get("moral_lesson", "N/A")
            )
            
            # Call LLM
            logger.info("Calling LLM to infer character details")
            response = self.llm.invoke(formatted_prompt)
            
            # Log the full response for debugging
            logger.debug(f"LLM Response: {response.content}")
            
            # Parse LLM response
            inferred_characters = self._parse_llm_response(response.content, character_names)
            
            if not inferred_characters:
                logger.warning("No characters were successfully inferred from LLM response")
                logger.info(f"LLM response was: {response.content[:500]}...")
            
            logger.info(f"Successfully inferred details for {len(inferred_characters)} characters")
            return inferred_characters
            
        except Exception as e:
            logger.error(f"Error inferring characters from segments: {e}")
            import traceback
            logger.debug(f"Traceback: {traceback.format_exc()}")
            # Return empty dict on error - caller will handle fallback
            return {}
    
    def _gather_character_contexts(
        self,
        character_names: List[str],
        script_segments: List[Dict[str, Any]]
    ) -> Dict[str, Dict[str, List[str]]]:
        """
        Gather context about each character from script segments.
        
        Args:
            character_names: List of character names
            script_segments: List of script segments
            
        Returns:
            Dictionary mapping character names to their contexts
        """
        character_contexts = {}
        
        for char_name in character_names:
            character_contexts[char_name] = {
                "appearances": [],
                "dialogues": [],
                "descriptions": []
            }
            
            for segment in script_segments:
                if char_name in segment.get("characters", []):
                    # Collect scene description
                    if segment.get("description"):
                        character_contexts[char_name]["descriptions"].append(
                            segment["description"]
                        )
                    # Collect dialogue
                    if segment.get("dialogue"):
                        character_contexts[char_name]["dialogues"].append(
                            segment["dialogue"]
                        )
                    # Collect narration
                    if segment.get("narration"):
                        character_contexts[char_name]["descriptions"].append(
                            segment["narration"]
                        )
        
        return character_contexts
    
    def _parse_llm_response(
        self,
        response_text: str,
        character_names: List[str]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Parse LLM response to extract character details.
        
        Args:
            response_text: Raw LLM response text
            character_names: List of expected character names
            
        Returns:
            Dictionary mapping character names to their details
        """
        try:
            # Extract JSON from response
            response_text = response_text.strip()
            
            # Try to extract JSON from markdown code blocks first
            # Pattern: ```json\n{...}\n``` or ```\n{...}\n```
            code_block_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response_text, re.DOTALL)
            if code_block_match:
                json_str = code_block_match.group(1)
            else:
                # Try to find JSON block without markdown
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    json_str = json_match.group()
                else:
                    logger.warning("Could not find JSON in LLM response")
                    logger.debug(f"Response text: {response_text[:200]}...")
                    return {}
            
            # Parse JSON
            try:
                inferred_chars = json.loads(json_str)
            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error: {e}")
                logger.debug(f"Attempted to parse: {json_str[:200]}...")
                return {}
            
            # Validate and return
            result = {}
            for char_name in character_names:
                if char_name in inferred_chars:
                    char_info = inferred_chars[char_name]
                    result[char_name] = {
                        "type": char_info.get("type", "character"),
                        "traits": char_info.get("traits", [])
                    }
                    logger.info(
                        f"Inferred {char_name}: type={char_info.get('type')}, "
                        f"traits={char_info.get('traits')}"
                    )
            
            return result
                
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing JSON from LLM response: {e}")
            logger.debug(f"Response text: {response_text[:500]}...")
            return {}
        except Exception as e:
            logger.error(f"Error parsing LLM response: {e}")
            logger.debug(f"Response text: {response_text[:500]}...")
            return {}
