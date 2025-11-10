# Multi-Agent Moral Story Video Workflow System

A production-grade multi-agent AI workflow system using LangChain and LangGraph to create animated moral story videos for children. This system uses six specialized agents that collaborate to transform a story context into a complete animated video.

## Features

- **Multi-Agent Architecture**: Six specialized agents working together
- **LangGraph Workflow**: State management and agent coordination
- **Child-Safe Content**: Content filtering at every stage
- **Error Handling**: Comprehensive retry logic and graceful degradation
- **Modular Design**: Easy to replace or modify agents
- **Production-Ready**: Logging, validation, and observability

## Architecture

The system consists of six specialized agents:

1. **Context Analyzer Agent**: Parses and validates input context
2. **Web Research Agent**: Gathers supplementary information
3. **Story Generation Agent**: Creates engaging moral stories
4. **Script Segmentation Agent**: Breaks story into visual scenes
5. **Character Design Agent**: Generates consistent character visuals
6. **Video Assembly Agent**: Compiles media into final video

## Installation

### Prerequisites

- Python 3.10 or higher
- FFmpeg (for video processing)
- API keys for:
  - OpenAI (for GPT-4 and DALL-E 3)
  - Tavily (for web search, optional)
  - ElevenLabs (for TTS, optional)

### Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd animation
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Install FFmpeg:
   - **Windows**: Download from [FFmpeg website](https://ffmpeg.org/download.html)
   - **macOS**: `brew install ffmpeg`
   - **Linux**: `sudo apt-get install ffmpeg`

4. Set up environment variables:
```bash
# Required
export OPENAI_API_KEY="your-openai-api-key"

# Optional
export TAVILY_API_KEY="your-tavily-api-key"
export ELEVENLABS_API_KEY="your-elevenlabs-api-key"
```

Or create a `.env` file:
```
OPENAI_API_KEY=your-openai-api-key
TAVILY_API_KEY=your-tavily-api-key
ELEVENLABS_API_KEY=your-elevenlabs-api-key
```

## Usage

### Basic Usage

Run with example input:
```bash
python main.py
```

### Using Input File

Create a JSON file with your story context:

```json
{
  "context": {
    "theme": "honesty",
    "characters": [
      {
        "name": "Leo",
        "type": "animal",
        "traits": ["brave", "curious"]
      },
      {
        "name": "Mia",
        "type": "animal",
        "traits": ["wise", "kind"]
      }
    ],
    "setting": "magical forest",
    "moral_lesson": "Honesty is the best policy, even when it's hard",
    "age_group": "6-8",
    "duration_minutes": 3
  },
  "preferences": {
    "art_style": "cartoon",
    "narration": true,
    "music": true
  }
}
```

Run with input file:
```bash
python main.py --input input.json
```

### Command-Line Options

```bash
python main.py [OPTIONS]

Options:
  -i, --input PATH       Path to input JSON file
  -o, --output PATH      Output directory (default: output/)
  --log-level LEVEL      Logging level (DEBUG, INFO, WARNING, ERROR)
  --log-file PATH        Path to log file
  --workflow-id ID       Optional workflow ID for tracking
  --estimate-cost        Estimate cost before execution
```

### Example Commands

```bash
# Run with input file and custom output directory
python main.py -i story.json -o videos/

# Run with debug logging
python main.py -i story.json --log-level DEBUG --log-file workflow.log

# Estimate cost before execution
python main.py -i story.json --estimate-cost
```

## Input Schema

### Context

- **theme** (string, required): Story theme (e.g., "honesty", "friendship", "courage")
- **characters** (array, required): List of character objects
  - **name** (string): Character name
  - **type** (string): Character type ("animal", "human", "fantasy")
  - **traits** (array): List of character traits
- **setting** (string, required): Story setting (e.g., "forest", "village", "school")
- **moral_lesson** (string, required): Moral lesson to convey
- **age_group** (string, required): Target age group ("3-5", "6-8", "9-12")
- **duration_minutes** (integer, optional): Target video length in minutes (1-10)

### Preferences

- **art_style** (string, optional): Art style ("cartoon", "watercolor", "3D", "2D")
- **narration** (boolean, optional): Include voice narration (default: true)
- **music** (boolean, optional): Include background music (default: true)

## Project Structure

```
project_root/
├── agents/              # Agent implementations
│   ├── context_analyzer.py
│   ├── web_researcher.py
│   ├── story_generator.py
│   ├── script_segmenter.py
│   ├── character_designer.py
│   └── video_assembler.py
├── graph/               # LangGraph workflow
│   ├── state.py
│   ├── workflow.py
│   └── nodes.py
├── tools/               # External API integrations
│   ├── search_tool.py
│   ├── image_gen_tool.py
│   └── video_tool.py
├── utils/               # Utilities
│   ├── validators.py
│   └── helpers.py
├── config.py            # Configuration management
├── main.py              # Main entry point
└── requirements.txt     # Dependencies
```

## Configuration

Configuration is managed through `config.py` and environment variables. Key settings:

- **LLM**: Model, temperature, max tokens
- **Image Generation**: Provider, quality, style
- **Text-to-Speech**: Provider, voice, language
- **Video**: Resolution, FPS, transitions
- **Retry**: Max retries, backoff strategy

## API Keys

### Required

- **OpenAI API Key**: For GPT-4 (story generation) and DALL-E 3 (image generation)
  - Get from: https://platform.openai.com/api-keys

### Optional

- **Tavily API Key**: For web search (graceful degradation if not provided)
  - Get from: https://tavily.com/
- **ElevenLabs API Key**: For high-quality TTS (falls back to gTTS if not provided)
  - Get from: https://elevenlabs.io/

## Cost Estimation

The system provides cost estimation before execution:

```bash
python main.py -i story.json --estimate-cost
```

Typical costs per video:
- **LLM Tokens**: $0.10 - $0.30
- **Image Generation**: $0.40 - $0.80 (10 images)
- **Web Search**: $0.01 - $0.05
- **Text-to-Speech**: $0.00 (gTTS) or $0.30 (ElevenLabs)
- **Total**: ~$0.50 - $1.50 per video

## Troubleshooting

### Common Issues

1. **FFmpeg not found**
   - Ensure FFmpeg is installed and in PATH
   - Test with: `ffmpeg -version`

2. **OpenAI API errors**
   - Check API key is set correctly
   - Verify API key has sufficient credits
   - Check rate limits

3. **Image generation fails**
   - Verify DALL-E 3 API access
   - Check image generation rate limits
   - Ensure sufficient API credits

4. **Video assembly fails**
   - Check FFmpeg installation
   - Verify image files exist
   - Check disk space

5. **Memory issues**
   - Reduce number of scenes
   - Lower image resolution
   - Process in smaller batches

### Debug Mode

Run with debug logging:
```bash
python main.py -i story.json --log-level DEBUG --log-file debug.log
```

### Error Handling

The system includes comprehensive error handling:
- Automatic retries with exponential backoff
- Graceful degradation (e.g., skip web search if API fails)
- Clear error messages in logs
- State persistence for recovery

## Development

### Running Tests

```bash
# Run with example input
python main.py

# Test with different configurations
python main.py -i test_inputs/honesty.json
```

### Extending the System

The modular architecture makes it easy to:
- Replace agents with custom implementations
- Add new agents to the workflow
- Modify state schema
- Add new tools and integrations

### Code Style

- Follow PEP 8
- Use type hints
- Include docstrings
- Write clear, maintainable code

## License

[Specify your license here]

## Contributing

[Specify contribution guidelines here]

## Support

For issues and questions:
- Check the troubleshooting section
- Review logs for error messages
- Open an issue on GitHub

## Acknowledgments

- LangChain and LangGraph for workflow orchestration
- OpenAI for GPT-4 and DALL-E 3
- MoviePy for video processing
- Tavily for web search

