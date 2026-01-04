# LLM Configuration Guide

## Overview

The animation workflow now supports **separate LLM configurations** for the `script_segmenter` and `character_designer` agents. This allows you to use different models, API keys, or settings for each agent.

## Configuration Options

### Default Behavior (Backward Compatible)

If you don't set agent-specific environment variables, both agents will use the default `OPENAI_API_KEY` and `OPENAI_BASE_URL` settings. This maintains backward compatibility with existing `.env` files.

### Agent-Specific Configuration

You can now configure each agent independently using these environment variables:

#### Script Segmenter Agent

```bash
SCRIPT_SEGMENTER_API_KEY=<your-api-key>
SCRIPT_SEGMENTER_BASE_URL=<base-url>
SCRIPT_SEGMENTER_MODEL=gpt-4-turbo
SCRIPT_SEGMENTER_TEMPERATURE=0.7
SCRIPT_SEGMENTER_MAX_TOKENS=12000
```

#### Character Designer Agent

```bash
CHARACTER_DESIGNER_API_KEY=<your-api-key>
CHARACTER_DESIGNER_BASE_URL=<base-url>
CHARACTER_DESIGNER_MODEL=gpt-4-turbo
CHARACTER_DESIGNER_TEMPERATURE=0.7
CHARACTER_DESIGNER_MAX_TOKENS=12000
```

## Use Cases

### 1. Different API Keys for Cost Management

Use separate API keys to track costs per agent:

```bash
# General fallback
OPENAI_API_KEY=sk-general-key

# Script segmenter uses a different account
SCRIPT_SEGMENTER_API_KEY=sk-segmenter-key

# Character designer uses the general key (not specified)
```

### 2. Different Models for Different Tasks

Use a more powerful model for script segmentation and a faster/cheaper model for character design:

```bash
OPENAI_API_KEY=sk-your-key
SCRIPT_SEGMENTER_MODEL=gpt-4-turbo
CHARACTER_DESIGNER_MODEL=gpt-3.5-turbo
```

### 3. Different Base URLs (e.g., OpenRouter)

Route different agents through different endpoints:

```bash
# Script segmenter uses OpenRouter
SCRIPT_SEGMENTER_API_KEY=sk-or-key
SCRIPT_SEGMENTER_BASE_URL=https://openrouter.ai/api/v1
SCRIPT_SEGMENTER_MODEL=anthropic/claude-3-opus

# Character designer uses OpenAI directly
CHARACTER_DESIGNER_API_KEY=sk-openai-key
CHARACTER_DESIGNER_BASE_URL=https://api.openai.com/v1
CHARACTER_DESIGNER_MODEL=gpt-4-turbo
```

### 4. Different Temperature Settings

Fine-tune creativity for each agent:

```bash
OPENAI_API_KEY=sk-your-key

# Script segmenter needs to be more precise
SCRIPT_SEGMENTER_TEMPERATURE=0.3

# Character designer can be more creative
CHARACTER_DESIGNER_TEMPERATURE=0.9
```

## Fallback Behavior

Each agent-specific setting has a fallback chain:

1. **Agent-specific environment variable** (e.g., `SCRIPT_SEGMENTER_API_KEY`)
2. **General environment variable** (e.g., `OPENAI_API_KEY`)
3. **Default value in code** (e.g., `gpt-4-turbo`)

This means you only need to set the variables you want to override.

## Configuration Classes

The following configuration classes are available in `config.py`:

- `LLMConfig` - General LLM configuration (used by other agents)
- `ScriptSegmenterLLMConfig` - Script Segmenter specific configuration
- `CharacterDesignerLLMConfig` - Character Designer specific configuration

## Example `.env` File

```bash
# Required: General OpenAI configuration
OPENAI_API_KEY=sk-your-openai-key
OPENAI_BASE_URL=https://api.openai.com/v1

# Optional: Script Segmenter overrides
SCRIPT_SEGMENTER_MODEL=gpt-4-turbo
SCRIPT_SEGMENTER_MAX_TOKENS=15000

# Optional: Character Designer overrides
CHARACTER_DESIGNER_TEMPERATURE=0.8

# Other services
TAVILY_API_KEY=tvly-your-key
IMAGEMAGICK_BINARY="C:\Program Files\ImageMagick-7.1.2-Q16-HDRI\magick.exe"
```

## Migration from Previous Setup

No changes are required! Your existing `.env` file will continue to work. Both agents will use the `OPENAI_API_KEY` and `OPENAI_BASE_URL` settings by default.

If you want to customize settings for specific agents, simply add the relevant environment variables to your `.env` file.
