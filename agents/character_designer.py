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

For each character, provide a detailed visual design description suitable for image generation.
Focus on physical appearance, clothing, colors, and distinctive features that match their personality traits.

**IMPORTANT**: Some characters may not have predefined traits. For these characters, infer appropriate 
personality traits and visual characteristics based on their type and role in the story context.

Format your response as follows for each character:
**[Character Name]**: [Detailed visual description including character type, physical features, clothing, colors, and personality-reflecting visual elements]

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
            
            # Use LLM to generate enhanced character design descriptions
            character_descriptions = {}
            
            if characters:
                try:
                    # Create prompt using the defined system and human prompts
                    prompt = ChatPromptTemplate.from_messages([
                        SystemMessagePromptTemplate.from_template(self.system_prompt),
                        HumanMessagePromptTemplate.from_template(self.human_prompt)
                    ])
                    
                    # Format characters for LLM input
                    characters_str = "\n".join([
                        f"- {char.get('name', 'Unknown')}: {char.get('type', 'character')} with traits: {', '.join(char.get('traits', []))}"
                        for char in characters
                    ])
                    
                    # Format context for LLM
                    context_str = f"Theme: {context.get('theme', 'N/A')}\nSetting: {context.get('setting', 'N/A')}\nMoral Lesson: {context.get('moral_lesson', 'N/A')}"
                    
                    # Format prompt with input
                    formatted_prompt = prompt.format_messages(
                        characters=characters_str,
                        context=context_str,
                        art_style=art_style,
                        age_group=age_group
                    )
                    
                    # Call LLM
                    logger.info("Generating character designs with LLM")
                    response = self.llm.invoke(formatted_prompt)
                    
                    # Parse LLM response to extract character descriptions
                    llm_descriptions = self._parse_llm_character_response(response.content, characters)
                    
                except Exception as e:
                    logger.warning(f"LLM character design generation failed: {e}. Using fallback method.")
                    llm_descriptions = {}
            else:
                llm_descriptions = {}
            
            # Generate character descriptions and reference images
            for char in characters:
                char_name = char.get("name", "Unknown")
                char_type = char.get("type", "unknown")
                traits = char.get("traits", [])
                
                # Use LLM-generated description if available, otherwise create basic prompt
                if char_name in llm_descriptions:
                    design_prompt = llm_descriptions[char_name]
                else:
                    design_prompt = self._create_design_prompt(char, art_style, age_group)
                
                # Generate character reference image
                logger.info(f"Generating reference image for {char_name}")
                reference_image_path = self.image_tool.generate_character_reference(
                    character_name=char_name,
                    character_description=design_prompt,
                    traits=traits,
                    style=art_style
                )
                
                # Analyze reference image with GPT-4 Vision to get detailed visual description
                visual_analysis = None
                if reference_image_path:
                    visual_analysis = self.image_tool.analyze_character_image(
                        image_path=reference_image_path,
                        character_name=char_name,
                        character_type=char_type
                    )
                
                character_descriptions[char_name] = {
                    "name": char_name,
                    "type": char_type,
                    "traits": traits,
                    "description": design_prompt,
                    "design_prompt": design_prompt,
                    "visual_analysis": visual_analysis,  # Detailed description from GPT-4 Vision
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
                scene_narration = segment.get("narration", "")
                characters = segment.get("characters", [])
                setting = segment.get("setting", context.get("setting", ""))
                emotions = segment.get("emotions", [])
                
                # Build complete character reference details with type, traits, and visual description
                character_references = {}
                for char_name in characters:
                    if char_name in character_descriptions:
                        char_desc = character_descriptions[char_name]
                        
                        # Build comprehensive character reference
                        char_type = char_desc.get("type", "character")
                        traits = char_desc.get("traits", [])
                        
                        # Prioritize visual analysis from reference image if available
                        visual_description = ""
                        if char_desc.get("visual_analysis"):
                            visual_description = char_desc["visual_analysis"]
                        elif char_desc.get("description"):
                            visual_description = char_desc["description"]
                        
                        # Create complete character reference dictionary
                        character_references[char_name] = {
                            "type": char_type,
                            "traits": traits,
                            "visual_description": visual_description
                        }
                        
                        logger.debug(f"Scene {scene_number} - Character {char_name}: type={char_type}, traits={traits[:3]}, has_visual_desc={bool(visual_description)}")
                
                logger.info(f"Generating image for scene {scene_number} with {len(character_references)} character(s)")
                
                # Generate scene image with complete character details
                image_path = self.image_tool.generate_scene_image(
                    scene_description=scene_description,
                    scene_narration=scene_narration,
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

    def _parse_llm_character_response(
        self,
        llm_response: str,
        characters: List[Dict[str, Any]]
    ) -> Dict[str, str]:
        """
        Parse LLM response to extract character design descriptions.
        
        Args:
            llm_response: Raw LLM response text
            characters: List of character dictionaries
            
        Returns:
            Dictionary mapping character names to design descriptions
        """
        import re
        
        character_designs = {}
        
        try:
            # Try to parse structured response
            # Expected format: Character name followed by description
            for char in characters:
                char_name = char.get("name", "Unknown")
                
                # Look for patterns like "CharacterName:" or "- CharacterName:" followed by description
                patterns = [
                    rf"{char_name}[:\-]\s*(.+?)(?=\n\n|\n[A-Z]|$)",  # Name: description
                    rf"\*\*{char_name}\*\*[:\-]?\s*(.+?)(?=\n\n|\n\*\*|$)",  # **Name**: description
                    rf"#{1,3}\s*{char_name}[:\-]?\s*(.+?)(?=\n#|\n\n|$)",  # # Name: description
                ]
                
                for pattern in patterns:
                    match = re.search(pattern, llm_response, re.DOTALL | re.IGNORECASE)
                    if match:
                        description = match.group(1).strip()
                        # Clean up the description
                        description = re.sub(r'\n+', ' ', description)  # Replace newlines with spaces
                        description = re.sub(r'\s+', ' ', description)  # Normalize whitespace
                        character_designs[char_name] = description
                        break
            
            # If we didn't find structured descriptions, try to extract from general text
            if not character_designs:
                logger.warning("Could not parse structured character descriptions from LLM response")
                # Return empty dict to fall back to basic prompt generation
                
        except Exception as e:
            logger.warning(f"Error parsing LLM character response: {e}")
        
        return character_designs
