"""Image generation tool with DALL-E 3 API integration."""

import time
import logging
import requests
from pathlib import Path
from typing import Optional, Dict, Any, List
from PIL import Image
import io

from config import get_config
from utils.helpers import get_temp_path

logger = logging.getLogger(__name__)


class ImageGenerationTool:
    """Image generation tool with DALL-E 3 API."""
    
    def __init__(self):
        """Initialize image generation tool."""
        self.config = get_config()
        self.openai_client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize OpenAI client for DALL-E."""
        try:
            if self.config.image_gen.provider == "dalle3" and self.config.image_gen.api_key:
                from openai import OpenAI
                self.openai_client = OpenAI(api_key=self.config.image_gen.api_key)
                logger.info("OpenAI client initialized for image generation")
            else:
                logger.warning("DALL-E 3 API key not found. Image generation will be disabled.")
        except ImportError:
            logger.error("OpenAI library not installed")
        except Exception as e:
            logger.error(f"Error initializing OpenAI client: {e}")
    
    def generate_image(
        self,
        prompt: str,
        character_name: Optional[str] = None,
        scene_number: Optional[int] = None,
        style: Optional[str] = None,
        output_path: Optional[Path] = None
    ) -> Optional[Path]:
        """
        Generate an image using DALL-E 3.
        
        Args:
            prompt: Image generation prompt
            character_name: Optional character name for consistency
            scene_number: Optional scene number for filename
            style: Optional art style override
            output_path: Optional output path (auto-generated if not provided)
            
        Returns:
            Path to generated image file, or None if generation failed
        """
        if not self.openai_client:
            logger.error("OpenAI client not available")
            return None
        
        # Enhance prompt for child-friendly content
        enhanced_prompt = self._enhance_prompt(prompt, style)
        
        try:
            logger.info(f"Generating image with prompt: {enhanced_prompt[:100]}...")
            
            # Call DALL-E 3 API
            response = self.openai_client.images.generate(
                model=self.config.image_gen.model,
                prompt=enhanced_prompt,
                size=self.config.image_gen.size,
                quality=self.config.image_gen.quality,
                style=self.config.image_gen.style,
                n=1,
            )
            
            # Get image URL
            image_url = response.data[0].url
            
            # Download image
            image_data = requests.get(image_url).content
            
            # Determine output path
            if output_path is None:
                filename = f"scene_{scene_number}.png" if scene_number else "image.png"
                if character_name:
                    filename = f"{character_name}_{filename}"
                output_path = get_temp_path(filename, "images")
            
            # Save image
            with open(output_path, "wb") as f:
                f.write(image_data)
            
            # Resize to 1920x1080 if needed
            self._resize_image(output_path, target_size=(1920, 1080))
            
            logger.info(f"Image generated and saved to: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error generating image: {e}")
            return None
    
    def analyze_character_image(
        self,
        image_path: Path,
        character_name: str,
        character_type: str
    ) -> Optional[str]:
        """
        Analyze a character reference image using GPT-4 Vision to extract detailed visual description.
        
        Args:
            image_path: Path to character reference image
            character_name: Name of the character
            character_type: Type of character (e.g., rabbit, fox)
            
        Returns:
            Detailed visual description string, or None if analysis failed
        """
        if not self.openai_client:
            logger.error("OpenAI client not available")
            return None
        
        if not image_path or not image_path.exists():
            logger.warning(f"Character reference image not found: {image_path}")
            return None
        
        try:
            import base64
            
            logger.info(f"Analyzing character reference image for {character_name}")
            
            # Read and encode image
            with open(image_path, "rb") as image_file:
                image_data = base64.b64encode(image_file.read()).decode('utf-8')
            
            # Create vision prompt
            vision_prompt = f"""Analyze this character reference image for {character_name}, a {character_type} character.

Provide a detailed visual description that includes:
1. Physical appearance (body shape, size, proportions)
2. Colors (fur/skin color, eye color, etc.)
3. Distinctive features (ears, tail, facial features, etc.)
4. Clothing and accessories (if any)
5. Art style and visual characteristics
6. Overall impression and personality conveyed through appearance

Format the description as a single paragraph suitable for image generation prompts.
Focus on concrete visual details that will ensure consistency across multiple scenes."""

            # Call GPT-4 Vision
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",  # GPT-4 Vision model
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": vision_prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{image_data}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=500
            )
            
            visual_description = response.choices[0].message.content.strip()
            
            logger.info(f"Character visual analysis complete for {character_name}")
            logger.debug(f"Visual description: {visual_description[:100]}...")
            
            return visual_description
            
        except Exception as e:
            logger.error(f"Error analyzing character image: {e}")
            return None
    
    def _enhance_prompt(self, prompt: str, style: Optional[str] = None) -> str:
        """
        Enhance prompt for child-friendly, consistent image generation.
        
        Args:
            prompt: Original prompt
            style: Optional art style
            
        Returns:
            Enhanced prompt
        """
        # Base enhancements for child-friendly content
        enhancements = [
            "child-friendly",
            "cartoon style",
            "bright and colorful",
            "safe for children",
            "wholesome",
        ]
        
        # Add style if specified
        if style:
            enhancements.append(style)
        elif self.config.image_gen.style:
            enhancements.append(self.config.image_gen.style)
        
        # Combine enhancements
        enhanced = f"{prompt}, {', '.join(enhancements)}, high quality, detailed"
        
        # Ensure prompt is within DALL-E 3 limits (4000 characters)
        if len(enhanced) > 4000:
            enhanced = prompt[:3500] + ", " + ", ".join(enhancements[:3])
        
        return enhanced
    
    def _resize_image(self, image_path: Path, target_size: tuple[int, int]) -> None:
        """
        Resize image to target size while maintaining aspect ratio.
        
        Args:
            image_path: Path to image file
            target_size: Target size (width, height)
        """
        try:
            with Image.open(image_path) as img:
                # Calculate new size maintaining aspect ratio
                img.thumbnail(target_size, Image.Resampling.LANCZOS)
                
                # Create new image with target size and paste resized image
                new_img = Image.new("RGB", target_size, (255, 255, 255))
                
                # Center the image
                x_offset = (target_size[0] - img.size[0]) // 2
                y_offset = (target_size[1] - img.size[1]) // 2
                new_img.paste(img, (x_offset, y_offset))
                
                # Save resized image
                new_img.save(image_path, "PNG", quality=95)
                
        except Exception as e:
            logger.warning(f"Error resizing image: {e}")
    
    def generate_character_reference(
        self,
        character_name: str,
        character_description: str,
        traits: List[str],
        style: Optional[str] = None
    ) -> Optional[Path]:
        """
        Generate a character reference sheet for consistency.
        
        Args:
            character_name: Name of the character
            character_description: Description of the character
            traits: List of character traits
            style: Optional art style
            
        Returns:
            Path to character reference image, or None if generation failed
        """
        # Create detailed prompt for character reference
        traits_str = ", ".join(traits)
        prompt = (
            f"Character reference sheet for {character_name}, "
            f"{character_description}, "
            f"traits: {traits_str}, "
            f"multiple poses and expressions, "
            f"front view, side view, full body, "
            f"consistent design, character sheet style"
        )
        
        output_path = get_temp_path(f"character_ref_{character_name}.png", "images")
        
        return self.generate_image(
            prompt=prompt,
            character_name=character_name,
            style=style,
            output_path=output_path
        )
    
    def generate_scene_image(
        self,
        scene_description: str,
        scene_narration: str,
        characters: List[str],
        setting: str,
        emotions: List[str],
        scene_number: int,
        character_references: Optional[Dict[str, Dict[str, Any]]] = None,
        scene_background: Optional[str] = None,
        style: Optional[str] = None
    ) -> Optional[Path]:
        """
        Generate an image for a specific scene.
        
        Args:
            scene_description: Description of the scene
            scene_narration: Narration of the scene
            characters: List of character names in the scene
            setting: Brief setting description (1-2 words)
            emotions: List of emotions to convey
            scene_number: Scene number
            character_references: Optional dict mapping character names to character detail dicts
                                 Each dict should contain: 'type', 'traits', 'visual_description'
            scene_background: Optional detailed background description (2-3 sentences)
            style: Optional art style
            
        Returns:
            Path to generated scene image, or None if generation failed
        """
        # Build comprehensive scene prompt with character details FIRST for consistency
        emotions_str = ", ".join(emotions) if emotions else "neutral"
        
        # Use detailed scene_background if provided, otherwise fall back to brief setting
        background_description = scene_background if scene_background else setting
        
        # Start with character details to ensure DALL-E prioritizes them
        if character_references and characters:
            # Build detailed character descriptions at the start
            char_details = []
            for char_name in characters:
                if char_name in character_references:
                    char_info = character_references[char_name]
                    
                    # Build comprehensive character description
                    char_type = char_info.get('type', 'character')
                    traits = char_info.get('traits', [])
                    visual_desc = char_info.get('visual_description', '')
                    
                    # Format: "Name (a type character with traits: trait1, trait2; visual details)"
                    char_desc_parts = [f"a {char_type}"]
                    
                    if traits:
                        traits_str = ", ".join(traits[:3])  # Limit to top 3 traits
                        char_desc_parts.append(f"with traits: {traits_str}")
                    
                    if visual_desc:
                        char_desc_parts.append(visual_desc)
                    
                    full_char_desc = " ".join(char_desc_parts)
                    char_details.append(f"{char_name} ({full_char_desc})")
                else:
                    char_details.append(char_name)
            
            characters_str = "; ".join(char_details)  # Use semicolon to separate characters
            
            prompt = (
                f"Characters: {characters_str}. "
                f"Scene: {scene_description}. "
                f"Narration: {scene_narration}. "
                f"Background: {background_description}. "
                f"Emotions: {emotions_str}. "
                f"Animated scene, clear composition, "
                f"characters visible and expressive"
            )
        else:
            # Fallback if no character references available
            characters_str = ", ".join(characters) if characters else "no characters"
            prompt = (
                f"Scene: {scene_description}, "
                f"Narration: {scene_narration}, "
                f"Characters: {characters_str}, "
                f"Background: {background_description}, "
                f"Emotions: {emotions_str}, "
                f"animated scene, clear composition, "
                f"characters visible and expressive"
            )
        
        output_path = get_temp_path(f"scene_{scene_number:03d}.png", "images")
        
        return self.generate_image(
            prompt=prompt,
            scene_number=scene_number,
            style=style,
            output_path=output_path
        )
    
    def generate_multiple_images(
        self,
        prompts: List[str],
        output_dir: Optional[Path] = None
    ) -> List[Optional[Path]]:
        """
        Generate multiple images.
        
        Args:
            prompts: List of prompts for image generation
            output_dir: Optional output directory
            
        Returns:
            List of paths to generated images
        """
        results = []
        
        for i, prompt in enumerate(prompts):
            logger.info(f"Generating image {i+1}/{len(prompts)}")
            
            if output_dir:
                output_path = output_dir / f"image_{i:03d}.png"
            else:
                output_path = None
            
            image_path = self.generate_image(
                prompt=prompt,
                scene_number=i,
                output_path=output_path
            )
            
            results.append(image_path)
            
            # Rate limiting - DALL-E 3 has rate limits
            if i < len(prompts) - 1:
                time.sleep(2)  # Wait 2 seconds between requests
        
        return results

