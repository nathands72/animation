# Image Generation - Quick Reference

## Choose Your Provider

### DALL-E 3 (Recommended for Quality)
```bash
IMAGE_GEN_PROVIDER=dalle3
OPENAI_API_KEY=sk-your-key
```

### Gemini Imagen (Google)
```bash
IMAGE_GEN_PROVIDER=gemini
GEMINI_API_KEY=your-key
```

### OpenRouter SD (Cost-Effective)
```bash
IMAGE_GEN_PROVIDER=openrouter-sd
OPENROUTER_API_KEY=sk-or-key
IMAGE_GEN_MODEL=stabilityai/stable-diffusion-xl-base-1.0
```

## Essential Environment Variables

| Variable | Purpose | Example |
|----------|---------|---------|
| `IMAGE_GEN_PROVIDER` | Choose provider | `dalle3` |
| `IMAGE_GEN_API_KEY` | Universal API key | `sk-your-key` |
| `IMAGE_GEN_MODEL` | Model to use | `dall-e-3` |
| `IMAGE_GEN_SIZE` | Image dimensions | `1024x1024` |

## Provider-Specific Keys

```bash
OPENAI_API_KEY=sk-...      # For DALL-E 3
GEMINI_API_KEY=...         # For Gemini
OPENROUTER_API_KEY=sk-...  # For OpenRouter
```

## Quick Setup

1. Copy `.env.sample` to `.env`
2. Set `IMAGE_GEN_PROVIDER`
3. Add appropriate API key
4. (Optional) Customize settings
5. Run your workflow!

## Installation

```bash
# Core (already installed)
pip install openai pillow requests

# For Gemini support
pip install google-generativeai
```

## Common Configurations

### High Quality DALL-E
```bash
IMAGE_GEN_PROVIDER=dalle3
OPENAI_API_KEY=sk-your-key
IMAGE_GEN_QUALITY=hd
IMAGE_GEN_SIZE=1792x1024
```

### Fast & Cheap OpenRouter
```bash
IMAGE_GEN_PROVIDER=openrouter-sd
OPENROUTER_API_KEY=sk-or-key
IMAGE_GEN_MODEL=runwayml/stable-diffusion-v1-5
SD_STEPS=20
```

## Troubleshooting

**Problem:** Images not generating
- ✅ Check API key is set
- ✅ Verify provider name is correct
- ✅ Check logs for errors

**Problem:** "Provider not supported"
- ✅ Valid providers: `dalle3`, `gemini`, `openrouter-sd`

**Problem:** Gemini not working
- ✅ Install: `pip install google-generativeai`

## Documentation

- 📖 Full Guide: `IMAGE_GEN_CONFIG_GUIDE.md`
- 📋 Implementation Details: `IMAGE_GEN_IMPLEMENTATION_SUMMARY.md`
- 🔧 LLM Config: `LLM_CONFIG_GUIDE.md`
