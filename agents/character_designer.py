"""Character Design Agent for generating consistent character visuals."""

import logging
from typing import Dict, Any, List, Optional
from pathlib import Path

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate

from config import get_config
from tools.image_gen_tool import ImageGenerationTool
from utils.helpers import get_temp_path

logger = logging.getLogger(__name__)


class CharacterDesignAgent:
    """Agent for generating consistent character visuals."""
    
    def __init__(self):
        """Initialize character design agent."""
        self.config = get_config()
        self.llm = ChatOpenAI(
            model_name=self.config.llm.model,
            temperature=self.config.llm.temperature,
            max_tokens=self.config.llm.max_tokens,
            api_key=self.config.llm.api_key
        )
        self.image_tool = ImageGenerationTool()
        
        # System prompt for character design
        self.system_prompt = """You are a character design expert for animated children's videos.

Your role is to create detailed character design prompts that:
1. Generate consistent character visuals across scenes
2. Are child-friendly and age-appropriate
3. Match the specified art style
4. Include character traits and personality
5. Are suitable for the target age group

For each character, create:
- Detailed visual description
- Design prompt for image generation
- Reference description for consistency

Ensure all designs are:
- Bright and colorful
- Child-friendly
- Consistent in style
- Appropriate for the target age group"""

        self.human_prompt = """Create character design descriptions for the following characters:

Characters:
{characters}

Context:
{context}

Art Style: {art_style}
Age Group: {age_group}

Create detailed character design descriptions and prompts for image generation.
Focus on consistency and child-friendly aesthetics."""

    def design_characters(
        self,
        context: Dict[str, Any],
        art_style: Optional[str] = None
    ) -> Dict[str, Dict[str, Any]]:
        """
        Generate character design descriptions and reference sheets.
        
        Args:
            context: Context dictionary with characters
            art_style: Optional art style override
            
        Returns:
            Dictionary mapping character names to design descriptions
        """
        try:
            logger.info("Designing characters")
            
            if art_style is None:
                art_style = self.config.image_gen.style or "cartoon"
            
            characters = context.get("characters", [])
            age_group = context.get("age_group", "6-8")
            
            # Generate character design descriptions using LLM
            character_descriptions = {}
            
            for char in characters:
                char_name = char.get("name", "Unknown")
                char_type = char.get("type", "unknown")
                traits = char.get("traits", [])
                
                # Create design prompt for this character
                design_prompt = self._create_design_prompt(char, art_style, age_group)
                
                # Generate character reference image
                logger.info(f"Generating reference image for {char_name}")
                reference_image_path = self.image_tool.generate_character_reference(
                    character_name=char_name,
                    character_description=design_prompt,
                    traits=traits,
                    style=art_style
                )
                
                character_descriptions[char_name] = {
                    "name": char_name,
                    "type": char_type,
                    "traits": traits,
                    "description": design_prompt,
                    "design_prompt": design_prompt,
                    "reference_image_path": str(reference_image_path) if reference_image_path else None,
                }
            
            logger.info(f"Character designs created for {len(character_descriptions)} characters")
            
            return character_descriptions
            
        except Exception as e:
            logger.error(f"Error designing characters: {e}")
            # Fallback: basic character descriptions without images
            logger.warning("Falling back to basic character descriptions")
            return self._fallback_character_descriptions(context)
    
    def generate_scene_images(
        self,
        script_segments: List[Dict[str, Any]],
        character_descriptions: Dict[str, Dict[str, Any]],
        context: Dict[str, Any],
        art_style: Optional[str] = None
    ) -> List[Optional[Path]]:
        """
        Generate images for each scene segment.
        
        Args:
            script_segments: List of scene segments
            character_descriptions: Character design descriptions
            context: Context dictionary
            art_style: Optional art style override
            
        Returns:
            List of paths to generated scene images
        """
        try:
            logger.info(f"Generating images for {len(script_segments)} scenes")
            
            if art_style is None:
                art_style = self.config.image_gen.style or "cartoon"
            
            scene_images = []
            
            for segment in script_segments:
                scene_number = segment.get("scene_number", 0)
                scene_description = segment.get("description", "")
                characters = segment.get("characters", [])
                setting = segment.get("setting", context.get("setting", ""))
                emotions = segment.get("emotions", [])
                
                # Get character reference descriptions
                character_references = {}
                for char_name in characters:
                    if char_name in character_descriptions:
                        char_desc = character_descriptions[char_name]
                        character_references[char_name] = char_desc.get("design_prompt", "")
                
                logger.info(f"Generating image for scene {scene_number}")
                
                # Generate scene image
                image_path = self.image_tool.generate_scene_image(
                    scene_description=scene_description,
                    characters=characters,
                    setting=setting,
                    emotions=emotions,
                    scene_number=scene_number,
                    character_references=character_references if character_references else None,
                    style=art_style
                )
                
                scene_images.append(image_path)
            
            logger.info(f"Generated {len([img for img in scene_images if img])} scene images")
            
            return scene_images
            
        except Exception as e:
            logger.error(f"Error generating scene images: {e}")
            return []
    
    def _create_design_prompt(
        self,
        character: Dict[str, Any],
        art_style: str,
        age_group: str
    ) -> str:
        """
        Create design prompt for a character.
        
        Args:
            character: Character dictionary
            art_style: Art style
            age_group: Target age group
            
        Returns:
            Design prompt string
        """
        name = character.get("name", "Unknown")
        char_type = character.get("type", "unknown")
        traits = character.get("traits", [])
        
        traits_str = ", ".join(traits) if traits else "friendly"
        
        prompt = (
            f"{name}, a {char_type} character, "
            f"with traits: {traits_str}, "
            f"{art_style} style, "
            f"bright and colorful, "
            f"child-friendly design, "
            f"appropriate for {age_group} age group, "
            f"expressive and animated"
        )
        
        return prompt
    
    def _fallback_character_descriptions(
        self,
        context: Dict[str, Any]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Create basic character descriptions without LLM or images.
        
        Args:
            context: Context dictionary
            
        Returns:
            Dictionary with basic character descriptions
        """
        characters = context.get("characters", [])
        character_descriptions = {}
        
        for char in characters:
            name = char.get("name", "Unknown")
            char_type = char.get("type", "unknown")
            traits = char.get("traits", [])
            
            character_descriptions[name] = {
                "name": name,
                "type": char_type,
                "traits": traits,
                "description": f"{name} is a {char_type} character with traits: {', '.join(traits) if traits else 'friendly'}",
                "design_prompt": f"{name}, {char_type}, cartoon style, bright and colorful, child-friendly",
                "reference_image_path": None,
            }
        
        return character_descriptions

