"""Image generation tool with multi-provider support (DALL-E 3, Gemini, OpenRouter SD)."""

import time
import logging
import requests
from pathlib import Path
from typing import Optional, Dict, Any, List
from PIL import Image
import io

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from config import get_config
from utils.helpers import get_temp_path, sanitize_text

logger = logging.getLogger(__name__)


class ImageGenerationTool:
    """Image generation tool with multi-provider support."""
    
    def __init__(self):
        """Initialize image generation tool."""
        self.config = get_config()
        self.client = None
        self.provider = self.config.image_gen.provider
        self._initialize_client()
        
        # Initialize LLM for prompt summarization
        self.llm = ChatOpenAI(
            model_name=self.config.llm.model,
            temperature=0.3,  # Lower temperature for more consistent summarization
            max_tokens=2000,
            api_key=self.config.llm.api_key,
            base_url=self.config.llm.base_url
        )
    
    def _initialize_client(self):
        """Initialize client based on configured provider."""
        try:
            if self.provider == "dalle3":
                self._initialize_dalle3_client()
            elif self.provider == "gemini":
                self._initialize_gemini_client()
            elif self.provider == "openrouter-sd":
                self._initialize_openrouter_client()
            elif self.provider == "stable-diffusion":
                self._initialize_sd_client()
            else:
                logger.error(f"Unsupported image generation provider: {self.provider}")
        except Exception as e:
            logger.error(f"Error initializing {self.provider} client: {e}")
    
    def _initialize_dalle3_client(self):
        """Initialize OpenAI client for DALL-E 3."""
        try:
            if not self.config.image_gen.api_key:
                logger.warning("DALL-E 3 API key not found. Image generation will be disabled.")
                return
            
            from openai import OpenAI
            
            # Build client parameters
            client_params = {"api_key": self.config.image_gen.api_key}
            
            # Add base_url if configured
            if self.config.image_gen.base_url:
                client_params["base_url"] = self.config.image_gen.base_url
            
            self.client = OpenAI(**client_params)
            logger.info("DALL-E 3 client initialized for image generation")
        except ImportError:
            logger.error("OpenAI library not installed. Install with: pip install openai")
        except Exception as e:
            logger.error(f"Error initializing DALL-E 3 client: {e}")
    
    def _initialize_gemini_client(self):
        """Initialize Google Gemini client for Imagen."""
        try:
            if not self.config.image_gen.api_key:
                logger.warning("Gemini API key not found. Image generation will be disabled.")
                return
            
            import google.generativeai as genai
            
            genai.configure(api_key=self.config.image_gen.api_key)
            self.client = genai
            logger.info("Gemini client initialized for image generation")
        except ImportError:
            logger.error("Google Generative AI library not installed. Install with: pip install google-generativeai")
        except Exception as e:
            logger.error(f"Error initializing Gemini client: {e}")
    
    def _initialize_openrouter_client(self):
        """Initialize OpenRouter client for Stable Diffusion."""
        try:
            if not self.config.image_gen.api_key:
                logger.warning("OpenRouter API key not found. Image generation will be disabled.")
                return
            
            from openai import OpenAI
            
            # OpenRouter uses OpenAI-compatible API
            self.client = OpenAI(
                api_key=self.config.image_gen.api_key,
                base_url=self.config.image_gen.base_url or "https://openrouter.ai/api/v1"
            )
            logger.info("OpenRouter client initialized for Stable Diffusion image generation")
        except ImportError:
            logger.error("OpenAI library not installed. Install with: pip install openai")
        except Exception as e:
            logger.error(f"Error initializing OpenRouter client: {e}")
    
    def _initialize_sd_client(self):
        """Initialize Stable Diffusion client (placeholder for custom SD API)."""
        logger.warning("Direct Stable Diffusion provider not yet implemented. Use openrouter-sd instead.")
        # This can be extended to support direct SD API endpoints
    
    def generate_image(
        self,
        prompt: str,
        character_name: Optional[str] = None,
        scene_number: Optional[int] = None,
        style: Optional[str] = None,
        output_path: Optional[Path] = None,
        character_reference_images: Optional[Dict[str, str]] = None
    ) -> Optional[Path]:
        """
        Generate an image using the configured provider.
        
        Args:
            prompt: Image generation prompt
            character_name: Optional character name for consistency
            scene_number: Optional scene number for filename
            style: Optional art style override
            output_path: Optional output path (auto-generated if not provided)
            character_reference_images: Optional dict mapping character names to reference image paths
                                       Used by providers that support image references (e.g., DALL-E 3, Gemini)
            
        Returns:
            Path to generated image file, or None if generation failed
        """
        if not self.client:
            logger.error(f"{self.provider} client not available")
            return None
        
        # Enhance prompt for child-friendly content
        enhanced_prompt = self._enhance_prompt(prompt, style)
        
        # Determine output path
        if output_path is None:
            filename = f"scene_{scene_number}.png" if scene_number else "image.png"
            if character_name:
                filename = f"{character_name}_{filename}"
            output_path = get_temp_path(filename, "images")
        
        # Route to provider-specific generation
        try:
            if self.provider == "dalle3":
                return self._generate_dalle3(enhanced_prompt, output_path, character_reference_images)
            elif self.provider == "gemini":
                return self._generate_gemini(enhanced_prompt, output_path, character_reference_images)
            elif self.provider == "openrouter-sd":
                return self._generate_openrouter_sd(enhanced_prompt, output_path, character_reference_images)
            else:
                logger.error(f"Image generation not implemented for provider: {self.provider}")
                return None
        except Exception as e:
            logger.error(f"Error generating image with {self.provider}: {e}")
            return None
    
    def _generate_dalle3(self, prompt: str, output_path: Path, character_reference_images: Optional[Dict[str, str]] = None) -> Optional[Path]:
        """Generate image using DALL-E 3.
        
        Note: DALL-E 3 API doesn't support direct reference image upload.
        Character consistency is achieved through detailed text descriptions in the prompt.
        
        Args:
            prompt: Enhanced generation prompt (already contains character descriptions)
            output_path: Path to save generated image
            character_reference_images: Optional dict (logged for info, but not used in API call)
        
        Returns:
            Path to generated image or None if failed
        """
        try:
            # Log reference image availability for debugging
            if character_reference_images:
                available_refs = [name for name, path in character_reference_images.items() 
                                 if path and Path(path).exists()]
                if available_refs:
                    logger.info(f"Character reference images available for: {', '.join(available_refs)}")
                    logger.info("Note: DALL-E 3 uses text descriptions from prompt (reference images not directly uploadable)")
            
            logger.info(f"Generating DALL-E 3 image with prompt: {prompt[:100]}...")
            
            # Call DALL-E 3 API (text-to-image only)
            response = self.client.images.generate(
                model=self.config.image_gen.model,
                prompt=prompt,
                size=self.config.image_gen.size,
                quality=self.config.image_gen.quality,
                style=self.config.image_gen.style,
                n=1,
            )
            
            # Get image URL
            image_url = response.data[0].url
            
            # Download image
            image_data = requests.get(image_url).content
            
            # Save image
            with open(output_path, "wb") as f:
                f.write(image_data)
            
            # Resize to 1920x1080 if needed
            self._resize_image(output_path, target_size=(1920, 1080))
            
            logger.info(f"DALL-E 3 image generated and saved to: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error generating DALL-E 3 image: {e}")
            return None
    
    def _generate_gemini(self, prompt: str, output_path: Path, character_reference_images: Optional[Dict[str, str]] = None) -> Optional[Path]:
        """Generate image using Google Gemini Imagen.
        
        Note: Gemini Imagen API doesn't support direct reference image upload.
        Character consistency is achieved through detailed text descriptions in the prompt.
        
        Args:
            prompt: Enhanced generation prompt (already contains character descriptions)
            output_path: Path to save generated image
            character_reference_images: Optional dict (logged for info, but not used in API call)
        
        Returns:
            Path to generated image or None if failed
        """
        try:
            # Log reference image availability for debugging
            if character_reference_images:
                available_refs = [name for name, path in character_reference_images.items() 
                                 if path and Path(path).exists()]
                if available_refs:
                    logger.info(f"Character reference images available for: {', '.join(available_refs)}")
                    logger.info("Note: Gemini Imagen uses text descriptions from prompt (reference images not directly uploadable)")
            
            logger.info(f"Generating Gemini image with prompt: {prompt[:100]}...")
            
            # Use Gemini's image generation (text-to-image only)
            model = self.client.ImageGenerationModel(self.config.image_gen.gemini_model)
            
            # Generate image
            response = model.generate_images(
                prompt=prompt,
                number_of_images=1,
                aspect_ratio="16:9",  # Closest to 1920x1080
            )
            
            # Save the first image
            if response.images:
                image = response.images[0]
                image.save(location=str(output_path))
                
                # Resize to exact 1920x1080
                self._resize_image(output_path, target_size=(1920, 1080))
                
                logger.info(f"Gemini image generated and saved to: {output_path}")
                return output_path
            else:
                logger.error("Gemini returned no images")
                return None
                
        except Exception as e:
            logger.error(f"Error generating Gemini image: {e}")
            return None
    
    def _generate_openrouter_sd(self, prompt: str, output_path: Path, character_reference_images: Optional[Dict[str, str]] = None) -> Optional[Path]:
        """Generate image using OpenRouter with Gemini or other image generation models.
        
        OpenRouter uses the chat completions endpoint for image generation with the modalities parameter.
        
        Args:
            prompt: Enhanced generation prompt (already contains character descriptions)
            output_path: Path to save generated image
            character_reference_images: Optional dict (logged for info, but not used in API call)
        
        Returns:
            Path to generated image or None if failed
        """
        try:
            # Log reference image availability for debugging
            if character_reference_images:
                available_refs = [name for name, path in character_reference_images.items() 
                                 if path and Path(path).exists()]
                if available_refs:
                    logger.info(f"Character reference images available for: {', '.join(available_refs)}")
                    logger.info("Note: OpenRouter uses text descriptions from prompt (reference images not directly uploadable)")
            
            logger.info(f"Generating OpenRouter image with prompt: {prompt[:100]}...")
            
            # OpenRouter uses chat completions endpoint for image generation
            # with modalities parameter to signal image generation
            response = self.client.chat.completions.create(
                model=self.config.image_gen.model,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                modalities=["image", "text"],  # Required for image generation
                # Optional: Configure image generation parameters
                # image_config={
                #     "aspect_ratio": "16:9",  # or "1:1", "4:3", etc.
                # }
            )
            
            # Extract image URL from response
            # OpenRouter returns images in the message.images attribute
            image_url = None
            if response.choices and len(response.choices) > 0:
                choice = response.choices[0]
                message = choice.message
                
                # Check for images attribute first (OpenRouter format)
                if hasattr(message, 'images') and message.images:
                    # Images is a list of image objects
                    if isinstance(message.images, list) and len(message.images) > 0:
                        first_image = message.images[0]
                        if isinstance(first_image, dict):
                            image_url = first_image.get('image_url', {}).get('url')
                
                # Fallback: Check content attribute (alternative format)
                if not image_url and hasattr(message, 'content'):
                    content = message.content
                    if isinstance(content, list):
                        for item in content:
                            if isinstance(item, dict) and item.get('type') == 'image_url':
                                image_url = item.get('image_url', {}).get('url')
                                break
                    elif isinstance(content, str) and content:
                        # Try to extract URL from text
                        import re
                        url_match = re.search(r'https?://[^\s]+', content)
                        if url_match:
                            image_url = url_match.group(0)
            
            if not image_url:
                logger.error("No image URL found in OpenRouter response")
                logger.debug(f"Response: {response}")
                return None
            
            # Download or decode image
            logger.info(f"Processing image from: {image_url[:50]}...")
            
            # Check if it's a base64 data URI
            if image_url.startswith('data:'):
                # Extract base64 data from data URI
                # Format: data:image/png;base64,<base64_data>
                import base64
                try:
                    # Split on comma to get the base64 part
                    header, base64_data = image_url.split(',', 1)
                    image_data = base64.b64decode(base64_data)
                    logger.info("Decoded base64 image data")
                except Exception as e:
                    logger.error(f"Error decoding base64 image: {e}")
                    return None
            else:
                # Regular HTTP URL - download the image
                try:
                    image_response = requests.get(image_url, timeout=30)
                    image_response.raise_for_status()
                    image_data = image_response.content
                    logger.info("Downloaded image from URL")
                except Exception as e:
                    logger.error(f"Error downloading image: {e}")
                    return None
            
            # Save image
            with open(output_path, "wb") as f:
                f.write(image_data)
            
            # Resize to 1920x1080 if needed
            self._resize_image(output_path, target_size=(1920, 1080))
            
            logger.info(f"OpenRouter image generated and saved to: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error generating OpenRouter image: {e}")
            import traceback
            logger.debug(f"Traceback: {traceback.format_exc()}")
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
        # Vision analysis only works with OpenAI models
        if self.provider != "dalle3" or not self.client:
            logger.warning(f"Character image analysis not supported for provider: {self.provider}")
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
            response = self.client.chat.completions.create(
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
        if len(enhanced) > 4000: #TODO: summarize prompt using LLM
            print(f"Prompt length exceeded DALL-E 3 limits. Prompt has been truncated. Original length: {len(enhanced)}")
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
    
    def summarize_character_descriptions(self, characters_str: str, max_length: int = 2000) -> str:
        """
        Summarize character descriptions using LLM if they exceed max_length.
        
        Args:
            characters_str: Full character descriptions string
            max_length: Maximum allowed length before summarization
            
        Returns:
            Original or summarized character descriptions
        """
        if len(characters_str) <= max_length:
            return characters_str
        
        try:
            logger.info(f"Character descriptions too long ({len(characters_str)} chars), summarizing with LLM...")
            
            # Create summarization prompt
            prompt = ChatPromptTemplate.from_messages([
                ("system", """You are an expert at condensing character descriptions for image generation.
Your task is to summarize character descriptions while preserving ALL essential visual details needed for consistent image generation.

CRITICAL: Keep these details for each character:
- Character name and type
- Physical appearance (body shape, size, colors)
- Distinctive features (ears, tail, facial features, clothing)
- Key personality traits that affect appearance
- Art style characteristics

Remove redundant phrases and verbose explanations, but NEVER remove visual details."""),
                ("human", """Summarize the following character descriptions to approximately {target_length} characters while preserving all essential visual details:

{characters_str}

Provide a concise version that maintains character consistency for image generation.""")
            ])
            
            # Calculate target length (aim for 80% of max to leave room)
            target_length = int(max_length * 0.8)
            
            # Format and invoke LLM
            formatted_prompt = prompt.format_messages(
                characters_str=characters_str,
                target_length=target_length
            )
            
            response = self.llm.invoke(formatted_prompt)
            summarized = sanitize_text(response.content).strip()
            
            logger.info(f"Summarized character descriptions from {len(characters_str)} to {len(summarized)} characters")
            
            return summarized
            
        except Exception as e:
            logger.error(f"Error summarizing character descriptions: {e}")
            # Fallback: simple truncation with ellipsis
            logger.warning(f"Falling back to simple truncation at {max_length} characters")
            return characters_str[:max_length - 3] + "..."
    
    
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
                                 Each dict should contain: 'character_detail', 'reference_image_path'
            scene_background: Optional detailed background description (2-3 sentences)
            style: Optional art style
            
        Returns:
            Path to generated scene image, or None if generation failed
        """
        # Build comprehensive scene prompt with character details FIRST for consistency
        emotions_str = ", ".join(emotions) if emotions else "neutral"
        
        # Use detailed scene_background if provided, otherwise fall back to brief setting
        background_description = f"{setting} -> {scene_background}"
        
        # Extract character reference image paths for providers that support them
        character_reference_images = {}
        if character_references and characters:
            for char_name in characters:
                if char_name in character_references:
                    ref_image_path = character_references[char_name].get('reference_image_path')
                    if ref_image_path:
                        character_reference_images[char_name] = ref_image_path
        
        # Start with character details to ensure image generator prioritizes them
        if character_references and characters:
            # Build detailed character descriptions at the start
            char_details = []
            for char_name in characters:
                if char_name in character_references:
                    char_info = character_references[char_name]
                    character_detail = char_info.get('character_detail', char_name)
                    char_details.append(character_detail)
                else:
                    char_details.append(char_name)
            
            characters_str = "; ".join(char_details)  # Use semicolon to separate characters
            
            # Summarize character descriptions if too long
            characters_str = self.summarize_character_descriptions(characters_str, max_length=2000)
        else:
            # Fallback if no character references available
            characters_str = ", ".join(characters) if characters else "no characters"

        prompt = " ".join([f"**Scene**: {scene_description}, \n\n",
            f"**Narration**: {scene_narration}, \n\n",
            f"**Characters**: {characters_str}, \n\n",
            f"**Background**: {background_description}, \n\n",
            f"**Emotions**: {emotions_str}, \n\n",
            f"animated scene, clear composition, \n\n",
            f"characters visible and expressive"])
        
        output_path = get_temp_path(f"scene_{scene_number:03d}.png", "images")
        
        # Pass character reference images to generate_image
        return self.generate_image(
            prompt=prompt,
            scene_number=scene_number,
            style=style,
            output_path=output_path,
            character_reference_images=character_reference_images if character_reference_images else None
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

