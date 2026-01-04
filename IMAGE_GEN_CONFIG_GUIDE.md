# Image Generation Configuration Guide

## Overview

The animation workflow now supports **multiple image generation providers** with full configuration from `.env` file. You can choose between:

- **DALL-E 3** (OpenAI)
- **Gemini Imagen** (Google)
- **OpenRouter Stable Diffusion**
- **Stable Diffusion** (direct API - placeholder for future implementation)

## Quick Start

### Using DALL-E 3 (Default)

```bash
IMAGE_GEN_PROVIDER=dalle3
OPENAI_API_KEY=sk-your-openai-key
IMAGE_GEN_MODEL=dall-e-3
IMAGE_GEN_SIZE=1024x1024
IMAGE_GEN_QUALITY=standard
IMAGE_GEN_STYLE=vivid
```

### Using Gemini Imagen

```bash
IMAGE_GEN_PROVIDER=gemini
GEMINI_API_KEY=your-gemini-api-key
GEMINI_IMAGE_MODEL=imagen-3.0-generate-001
```

### Using OpenRouter Stable Diffusion

```bash
IMAGE_GEN_PROVIDER=openrouter-sd
OPENROUTER_API_KEY=sk-or-your-key
IMAGE_GEN_MODEL=stabilityai/stable-diffusion-xl-base-1.0
IMAGE_GEN_SIZE=1024x1024
```

## Environment Variables Reference

### General Settings

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `IMAGE_GEN_PROVIDER` | Image generation provider | `dalle3` | No |
| `IMAGE_GEN_API_KEY` | Universal API key (falls back to provider-specific) | None | Yes* |
| `IMAGE_GEN_BASE_URL` | Base URL for API (auto-set for some providers) | None | No |
| `IMAGE_GEN_MODEL` | Model to use | `dall-e-3` | No |
| `IMAGE_GEN_SIZE` | Image size | `1024x1024` | No |
| `IMAGE_GEN_QUALITY` | Image quality (DALL-E only) | `standard` | No |
| `IMAGE_GEN_STYLE` | Image style (DALL-E only) | `vivid` | No |

*API key can be provided via provider-specific variables (see below)

### DALL-E 3 Settings

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key | None |
| `IMAGE_GEN_MODEL` | DALL-E model | `dall-e-3` |
| `IMAGE_GEN_SIZE` | Image size (`1024x1024`, `1792x1024`, `1024x1792`) | `1024x1024` |
| `IMAGE_GEN_QUALITY` | Quality (`standard`, `hd`) | `standard` |
| `IMAGE_GEN_STYLE` | Style (`vivid`, `natural`) | `vivid` |

### Gemini Imagen Settings

| Variable | Description | Default |
|----------|-------------|---------|
| `GEMINI_API_KEY` | Google Gemini API key | None |
| `GEMINI_IMAGE_MODEL` | Gemini image model | `imagen-3.0-generate-001` |
| `IMAGE_GEN_BASE_URL` | Gemini API base URL | `https://generativelanguage.googleapis.com/v1beta` |

### OpenRouter Stable Diffusion Settings

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENROUTER_API_KEY` | OpenRouter API key | None |
| `IMAGE_GEN_MODEL` | SD model on OpenRouter | Provider default |
| `IMAGE_GEN_BASE_URL` | OpenRouter base URL | `https://openrouter.ai/api/v1` |
| `SD_STEPS` | Number of diffusion steps | `30` |
| `SD_CFG_SCALE` | CFG scale for guidance | `7.0` |
| `SD_SAMPLER` | Sampler algorithm | `DPM++ 2M Karras` |

**Popular OpenRouter SD Models:**
- `stabilityai/stable-diffusion-xl-base-1.0`
- `stabilityai/stable-diffusion-2-1`
- `runwayml/stable-diffusion-v1-5`

## Configuration Examples

### Example 1: DALL-E 3 with High Quality

```bash
IMAGE_GEN_PROVIDER=dalle3
OPENAI_API_KEY=sk-your-key
IMAGE_GEN_MODEL=dall-e-3
IMAGE_GEN_SIZE=1792x1024
IMAGE_GEN_QUALITY=hd
IMAGE_GEN_STYLE=natural
```

### Example 2: Gemini Imagen

```bash
IMAGE_GEN_PROVIDER=gemini
GEMINI_API_KEY=your-gemini-key
GEMINI_IMAGE_MODEL=imagen-3.0-generate-001
```

### Example 3: OpenRouter with Custom SD Model

```bash
IMAGE_GEN_PROVIDER=openrouter-sd
OPENROUTER_API_KEY=sk-or-your-key
IMAGE_GEN_MODEL=stabilityai/stable-diffusion-xl-base-1.0
IMAGE_GEN_SIZE=1024x1024
SD_STEPS=50
SD_CFG_SCALE=8.5
SD_SAMPLER=Euler a
```

### Example 4: Using Custom Base URL (e.g., OpenAI via Proxy)

```bash
IMAGE_GEN_PROVIDER=dalle3
IMAGE_GEN_API_KEY=sk-your-key
IMAGE_GEN_BASE_URL=https://your-proxy.com/v1
IMAGE_GEN_MODEL=dall-e-3
```

## Provider Comparison

| Feature | DALL-E 3 | Gemini Imagen | OpenRouter SD |
|---------|----------|---------------|---------------|
| Quality | Excellent | Excellent | Very Good |
| Speed | Fast | Fast | Medium |
| Cost | $$$ | $$ | $ |
| Consistency | Very Good | Good | Good |
| Customization | Limited | Limited | High |
| Character Vision Analysis | ✅ Yes | ❌ No | ❌ No |

## API Key Fallback Chain

The system uses a smart fallback mechanism for API keys:

1. **`IMAGE_GEN_API_KEY`** - Universal override
2. **Provider-specific key** - `OPENAI_API_KEY`, `GEMINI_API_KEY`, or `OPENROUTER_API_KEY`
3. **Error** - If no key is found

Example:
```bash
# This works - uses OPENAI_API_KEY for DALL-E
IMAGE_GEN_PROVIDER=dalle3
OPENAI_API_KEY=sk-your-key

# This also works - IMAGE_GEN_API_KEY overrides
IMAGE_GEN_PROVIDER=dalle3
IMAGE_GEN_API_KEY=sk-different-key
OPENAI_API_KEY=sk-your-key  # Ignored for image gen
```

## Features by Provider

### DALL-E 3 Features
- ✅ High-quality image generation
- ✅ GPT-4 Vision character analysis
- ✅ Multiple size options
- ✅ Quality settings (standard/hd)
- ✅ Style settings (vivid/natural)

### Gemini Imagen Features
- ✅ High-quality image generation
- ✅ Aspect ratio control (16:9 for videos)
- ❌ No character vision analysis
- ⚠️ Requires Google Cloud setup

### OpenRouter SD Features
- ✅ Multiple SD model options
- ✅ Cost-effective
- ✅ Advanced parameters (steps, CFG, sampler)
- ❌ No character vision analysis
- ⚠️ Quality varies by model

## Troubleshooting

### Issue: "API key not found"

**Solution:** Set the appropriate API key:
```bash
# For DALL-E
OPENAI_API_KEY=sk-your-key

# For Gemini
GEMINI_API_KEY=your-gemini-key

# For OpenRouter
OPENROUTER_API_KEY=sk-or-your-key
```

### Issue: "Provider not supported"

**Solution:** Check your `IMAGE_GEN_PROVIDER` value. Valid options:
- `dalle3`
- `gemini`
- `openrouter-sd`
- `stable-diffusion` (not yet implemented)

### Issue: Images not generating with Gemini

**Solution:** Ensure you have the Google Generative AI library installed:
```bash
pip install google-generativeai
```

### Issue: Character analysis not working

**Solution:** Character vision analysis only works with DALL-E 3 provider. If using Gemini or OpenRouter, character descriptions will be text-based only.

## Migration Guide

### From Previous Setup

The new configuration is backward compatible. If you had:

```bash
OPENAI_API_KEY=sk-your-key
```

It will continue to work with DALL-E 3 as the default provider.

### Switching Providers

To switch from DALL-E to Gemini:

```bash
# Old (DALL-E 3)
IMAGE_GEN_PROVIDER=dalle3
OPENAI_API_KEY=sk-your-key

# New (Gemini)
IMAGE_GEN_PROVIDER=gemini
GEMINI_API_KEY=your-gemini-key
```

### Using Multiple Providers

You can keep multiple API keys configured and switch by changing `IMAGE_GEN_PROVIDER`:

```bash
# Keep all keys configured
OPENAI_API_KEY=sk-openai-key
GEMINI_API_KEY=gemini-key
OPENROUTER_API_KEY=sk-or-key

# Switch provider as needed
IMAGE_GEN_PROVIDER=dalle3  # or gemini, or openrouter-sd
```

## Best Practices

1. **For Production**: Use DALL-E 3 for best quality and consistency
2. **For Cost Savings**: Use OpenRouter SD with a good model
3. **For Experimentation**: Try different providers and compare results
4. **For Character Consistency**: Use DALL-E 3 (supports vision analysis)
5. **For Custom Styles**: Use OpenRouter SD with specific models

## Advanced Configuration

### Custom Stable Diffusion Parameters

Fine-tune SD generation:

```bash
IMAGE_GEN_PROVIDER=openrouter-sd
OPENROUTER_API_KEY=sk-or-your-key
IMAGE_GEN_MODEL=stabilityai/stable-diffusion-xl-base-1.0

# Advanced SD settings
SD_STEPS=50              # More steps = better quality (but slower)
SD_CFG_SCALE=8.5         # Higher = more prompt adherence
SD_SAMPLER=Euler a       # Different sampling algorithms
```

### Using Different Models for Different Tasks

While the system uses one provider at a time, you can create different `.env` files for different workflows:

```bash
# .env.dalle3
IMAGE_GEN_PROVIDER=dalle3
OPENAI_API_KEY=sk-your-key

# .env.gemini
IMAGE_GEN_PROVIDER=gemini
GEMINI_API_KEY=your-key

# Switch by copying the appropriate file
cp .env.dalle3 .env
```

## Getting API Keys

### OpenAI (DALL-E 3)
1. Visit https://platform.openai.com/api-keys
2. Create a new API key
3. Add billing information

### Google Gemini
1. Visit https://makersuite.google.com/app/apikey
2. Create a new API key
3. Enable the Generative AI API

### OpenRouter
1. Visit https://openrouter.ai/keys
2. Create a new API key
3. Add credits to your account

## Support

For issues or questions:
1. Check the logs for detailed error messages
2. Verify your API key is valid and has credits
3. Ensure required libraries are installed
4. Check provider-specific documentation
