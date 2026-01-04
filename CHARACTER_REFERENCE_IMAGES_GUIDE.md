# Character Reference Images - Implementation Guide

## Overview

The image generation system now supports **character reference images** to improve character consistency across scenes. When generating scene images, the system can use previously generated character reference images to ensure characters maintain their visual appearance.

## How It Works

### Provider Support

| Provider | Reference Image Support | Method |
|----------|------------------------|--------|
| **DALL-E 3** | ✅ Full Support | GPT-4 Vision analyzes reference images and enhances prompts |
| **Gemini** | ⚠️ Partial Support | Character context added to prompt (no direct image analysis) |
| **OpenRouter SD** | ⚠️ Partial Support | Character context added to prompt (no direct image analysis) |

### DALL-E 3 (Recommended)

DALL-E 3 provides the best character reference support through GPT-4 Vision:

1. **Reference Image Analysis**: When character reference images are provided, GPT-4 Vision analyzes each image
2. **Visual Description Extraction**: Extracts concise visual descriptions (2 sentences) focusing on:
   - Key physical features (body type, colors, distinctive traits)
   - Clothing and accessories
   - Art style
3. **Prompt Enhancement**: Prepends character descriptions to the scene prompt
4. **Consistent Generation**: DALL-E 3 uses enhanced prompt to maintain character consistency

**Example Flow:**
```
Character Reference Image → GPT-4 Vision Analysis → 
"Leo: A friendly lion cub with golden fur and bright blue eyes, 
wearing a red bandana. Cartoon style with soft, rounded features." →
Enhanced Scene Prompt → DALL-E 3 Generation
```

### Gemini & OpenRouter SD

These providers add character context to prompts but don't directly analyze reference images:

1. **Character Detection**: Identifies characters with reference images
2. **Context Addition**: Adds character names to prompt
3. **Text-Based Enhancement**: Relies on existing character descriptions in the prompt

## Usage

### Automatic Usage (Default)

Character reference images are automatically used when available. The `CharacterDesignAgent` generates reference images and stores paths in character descriptions:

```python
character_descriptions[char_name] = {
    "name": char_name,
    "type": char_type,
    "traits": traits,
    "description": design_prompt,
    "visual_analysis": visual_analysis,
    "reference_image_path": str(reference_image_path)  # ← Used automatically
}
```

When `generate_scene_image()` is called with `character_references`, it automatically:
1. Extracts reference image paths
2. Passes them to the image generation provider
3. Enhances prompts based on provider capabilities

### Manual Usage

You can also manually provide character reference images:

```python
from tools.image_gen_tool import ImageGenerationTool

image_tool = ImageGenerationTool()

# Prepare character reference images
character_ref_images = {
    "Leo": "/path/to/leo_reference.png",
    "Mia": "/path/to/mia_reference.png"
}

# Generate image with references
image_path = image_tool.generate_image(
    prompt="Leo and Mia playing in the forest",
    scene_number=1,
    character_reference_images=character_ref_images
)
```

## API Reference

### `generate_image()`

```python
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
        character_reference_images: Optional dict mapping character names to 
                                   reference image paths
    
    Returns:
        Path to generated image file, or None if generation failed
    """
```

### `generate_scene_image()`

```python
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
        character_references: Optional dict mapping character names to character 
                            detail dicts. Each dict should contain:
                            - 'type': Character type
                            - 'traits': List of traits
                            - 'visual_description': Visual description
                            - 'reference_image_path': Path to reference image
    """
```

## Implementation Details

### DALL-E 3 Reference Analysis

The `_analyze_reference_image_for_prompt()` method:

```python
def _analyze_reference_image_for_prompt(
    self, 
    image_path: str, 
    character_name: str
) -> Optional[str]:
    """
    Analyze a reference image to extract visual description.
    
    Process:
    1. Read and base64-encode the reference image
    2. Send to GPT-4 Vision with analysis prompt
    3. Extract concise visual description (max 2 sentences)
    4. Return description for prompt enhancement
    
    Returns:
        Concise visual description or None if analysis failed
    """
```

### Prompt Enhancement

**DALL-E 3 with References:**
```
Original Prompt:
"Scene: Leo discovers a golden feather in the forest"

Enhanced Prompt:
"Character visual references: Leo: A friendly lion cub with golden fur 
and bright blue eyes, wearing a red bandana. Cartoon style with soft, 
rounded features. Scene: Leo discovers a golden feather in the forest"
```

**Gemini/OpenRouter with References:**
```
Original Prompt:
"Scene: Leo discovers a golden feather in the forest"

Enhanced Prompt:
"Characters: Leo (as shown in reference). Scene: Leo discovers a 
golden feather in the forest"
```

## Benefits

### 1. **Improved Character Consistency**
- Characters maintain visual appearance across scenes
- Reduces variation in character design
- Better storytelling through consistent visuals

### 2. **Automatic Integration**
- No code changes needed in existing workflows
- Reference images used automatically when available
- Graceful degradation when references not available

### 3. **Provider-Specific Optimization**
- DALL-E 3: Full vision-based analysis
- Gemini/OpenRouter: Text-based context enhancement
- Each provider uses best available method

### 4. **Flexible Usage**
- Works with automatic character generation
- Supports manual reference image provision
- Optional - works without references too

## Best Practices

### 1. **Use DALL-E 3 for Best Results**
For maximum character consistency, use DALL-E 3 as your image generation provider:
```bash
IMAGE_GEN_PROVIDER=dalle3
```

### 2. **Generate Quality Reference Images**
Ensure character reference images are:
- High quality (1024x1024 or larger)
- Clear and well-lit
- Show character from multiple angles if possible
- Consistent with desired art style

### 3. **Provide Complete Character Information**
When using character references, include:
- Character type
- Visual traits
- Reference image path
- Visual analysis (if available)

### 4. **Monitor Logs**
Check logs to see reference image usage:
```
INFO: Using 2 character reference images for DALL-E 3
DEBUG: Reference image analysis for Leo: A friendly lion cub...
INFO: DALL-E 3 image generated and saved to: scene_001.png
```

## Troubleshooting

### Issue: Reference images not being used

**Check:**
1. Verify `reference_image_path` is in character_references dict
2. Ensure image files exist at specified paths
3. Check logs for "Using X character reference images" message

**Solution:**
```python
# Verify reference image path exists
if char_info.get('reference_image_path'):
    ref_path = Path(char_info['reference_image_path'])
    if ref_path.exists():
        print(f"✓ Reference image found: {ref_path}")
    else:
        print(f"✗ Reference image missing: {ref_path}")
```

### Issue: GPT-4 Vision analysis failing

**Symptoms:**
- Warning: "Could not analyze reference image for [character]"
- Characters not consistent despite references

**Solutions:**
1. Verify OpenAI API key has GPT-4 Vision access
2. Check image file format (PNG, JPEG supported)
3. Ensure image file size is reasonable (<20MB)
4. Check for base64 encoding errors in logs

### Issue: Inconsistent results with Gemini/OpenRouter

**Explanation:**
Gemini and OpenRouter SD don't support direct image analysis, so consistency may be lower than DALL-E 3.

**Solutions:**
1. Switch to DALL-E 3 for better consistency
2. Enhance text descriptions in character_references
3. Use more detailed visual_description fields

## Performance Considerations

### DALL-E 3
- **Additional API Calls**: One GPT-4 Vision call per character reference
- **Cost**: ~$0.01 per reference image analysis (GPT-4 Vision)
- **Time**: +1-2 seconds per reference image
- **Quality**: Excellent character consistency

### Gemini/OpenRouter
- **Additional API Calls**: None
- **Cost**: No additional cost
- **Time**: No additional time
- **Quality**: Basic character context only

## Example Workflow

```python
# 1. Character Designer generates reference images
character_descriptions = character_designer.design_characters(context)
# Each character now has reference_image_path

# 2. Scene images automatically use references
scene_images = character_designer.generate_scene_images(
    script_segments=segments,
    character_descriptions=character_descriptions,  # ← Contains reference paths
    context=context
)

# 3. Image generation tool automatically:
#    - Extracts reference image paths
#    - Analyzes images (DALL-E 3 only)
#    - Enhances prompts
#    - Generates consistent scene images
```

## Configuration

No additional configuration needed! The feature works automatically when:
1. Character reference images are generated
2. Reference paths are included in character_references
3. Scene images are generated with character_references

To disable reference image usage (if needed):
```python
# Don't pass character_references
image_path = image_tool.generate_scene_image(
    scene_description=desc,
    scene_narration=narr,
    characters=chars,
    setting=setting,
    emotions=emotions,
    scene_number=num,
    character_references=None  # ← Disables reference usage
)
```

## Future Enhancements

Potential improvements for future versions:

1. **Gemini Vision Integration**: Use Gemini's vision models for reference analysis
2. **Image-to-Image Generation**: Direct img2img for SD models
3. **Reference Image Caching**: Cache vision analysis results
4. **Multi-Reference Support**: Combine multiple reference images per character
5. **Style Transfer**: Apply reference image style to scenes

## Summary

Character reference images provide a powerful way to maintain visual consistency across your animated videos. With automatic integration and provider-specific optimizations, the system delivers the best possible results for each image generation provider while maintaining backward compatibility with existing workflows.
