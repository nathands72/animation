# Multi-Agent Moral Story Video Workflow System

A production-grade multi-agent AI workflow system using LangChain and LangGraph to create animated moral story videos for children. This system uses six specialized agents that collaborate to transform a story context into a complete animated video.

## Features

- **Multi-Agent Architecture**: Six specialized agents working together
- **LangGraph Workflow**: State management and agent coordination
- **Checkpoint & Resume**: Automatic progress saving and resume from any step
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

#### System Requirements

- **Python**: 3.10 or higher
- **Operating System**: Windows, macOS, or Linux
- **Disk Space**: At least 2GB free for temporary files and outputs
- **RAM**: Minimum 4GB (8GB recommended for smooth operation)

#### Required Software

1. **FFmpeg** (for video processing)
   - Required for video encoding and audio processing
   - Installation instructions below

2. **ImageMagick** (for text overlays and end cards)
   - **CRITICAL**: Required for creating moral message end cards
   - Without this, videos will be created without end cards
   - Installation instructions below

#### API Keys

**Required:**
- **OpenAI API Key**: For GPT-4 (story generation) and DALL-E 3 (image generation)
  - Get from: https://platform.openai.com/api-keys

**Optional:**
- **Tavily API Key**: For web search (graceful degradation if not provided)
  - Get from: https://tavily.com/
- **ElevenLabs API Key**: For high-quality TTS (falls back to gTTS if not provided)
  - Get from: https://elevenlabs.io/

### Setup

#### 1. Clone the Repository

```bash
git clone <repository-url>
cd animation
```

#### 2. Create Virtual Environment (Recommended)

```bash
# Windows
python -m venv animi-venv
animi-venv\Scripts\activate

# macOS/Linux
python3 -m venv animi-venv
source animi-venv/bin/activate
```

#### 3. Install Python Dependencies

```bash
pip install -r requirements.txt
```

#### 4. Install FFmpeg

**Windows:**
1. Download from [FFmpeg website](https://ffmpeg.org/download.html)
2. Extract to `C:\ffmpeg`
3. Add `C:\ffmpeg\bin` to your system PATH
4. Verify: `ffmpeg -version`

**macOS:**
```bash
brew install ffmpeg
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get update
sudo apt-get install ffmpeg
```

#### 5. Install ImageMagick (CRITICAL)

**Windows:**
1. Download from: https://imagemagick.org/script/download.php
   - Choose `ImageMagick-7.x.x-x-Q16-x64-dll.exe`
2. During installation, **check these options**:
   - ✅ **Install legacy utilities (e.g., convert)**
   - ✅ **Add application directory to your system path**
3. Restart your terminal/PowerShell
4. Verify: `magick -version`

**macOS:**
```bash
brew install imagemagick
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get update
sudo apt-get install imagemagick
```

> **Note:** If ImageMagick is not installed, videos will be created without moral message end cards. See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for details.

#### 6. Set Up Environment Variables

Create a `.env` file in the project root:

```bash
# Required
OPENAI_API_KEY=your-openai-api-key

# Optional
TAVILY_API_KEY=your-tavily-api-key
ELEVENLABS_API_KEY=your-elevenlabs-api-key

# Optional: Specify ImageMagick path if not in system PATH
# IMAGEMAGICK_BINARY=C:\Program Files\ImageMagick-7.1.1-Q16\magick.exe
```

Or set environment variables directly:

**Windows (PowerShell):**
```powershell
$env:OPENAI_API_KEY="your-openai-api-key"
$env:TAVILY_API_KEY="your-tavily-api-key"
$env:ELEVENLABS_API_KEY="your-elevenlabs-api-key"
```

**macOS/Linux:**
```bash
export OPENAI_API_KEY="your-openai-api-key"
export TAVILY_API_KEY="your-tavily-api-key"
export ELEVENLABS_API_KEY="your-elevenlabs-api-key"
```

#### 7. Verify Installation

Run these commands to verify your setup:

```bash
# Check Python packages
pip list | grep -E "moviepy|gtts|langchain|openai"

# Check system binaries
ffmpeg -version
magick -version

# Test the workflow (uses example input)
python main.py --estimate-cost
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
  -i, --input PATH            Path to input JSON file
  -o, --output PATH           Output directory (default: output/)
  --log-level LEVEL           Logging level (DEBUG, INFO, WARNING, ERROR)
  --log-file PATH             Path to log file
  --workflow-id ID            Workflow ID for tracking and checkpointing
  --estimate-cost             Estimate cost before execution
  
  Checkpoint & Resume:
  --resume                    Resume from latest checkpoint
  --resume-from-step STEP     Resume from specific step
  --checkpoint-path PATH      Resume from specific checkpoint file
  --list-checkpoints          List available checkpoints
  --no-checkpoint             Disable automatic checkpointing
```

### Example Commands

```bash
# Run with input file and custom output directory
python main.py -i story.json -o videos/

# Run with workflow ID (enables checkpointing)
python main.py -i story.json --workflow-id my-video-001

# Run with debug logging
python main.py -i story.json --log-level DEBUG --log-file workflow.log

# Estimate cost before execution
python main.py -i story.json --estimate-cost

# Resume from latest checkpoint
python main.py --workflow-id my-video-001 --resume

# Resume from specific step
python main.py --workflow-id my-video-001 --resume-from-step story_generator

# List available checkpoints
python main.py --workflow-id my-video-001 --list-checkpoints
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
│   ├── helpers.py
│   └── checkpoint_manager.py
├── docs/                # Documentation
│   └── checkpointing.md
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

## Checkpoint and Resume

The system automatically saves progress after each step, allowing you to resume from any point.

### Automatic Checkpointing

Checkpoints are automatically saved when using `--workflow-id`:

```bash
python main.py -i story.json --workflow-id my-video-001
```

Checkpoints are saved to `temp/checkpoints/{workflow_id}/` and include:
- Full workflow state at each step
- Intermediate outputs (story text, images, etc.)
- Metadata and timestamps

### Resume from Latest Checkpoint

If your workflow is interrupted or fails:

```bash
python main.py --workflow-id my-video-001 --resume
```

### Resume from Specific Step

To restart from a particular step (e.g., to regenerate the video):

```bash
python main.py --workflow-id my-video-001 --resume-from-step video_assembler
```

Available steps:
- `context_analyzer`
- `web_researcher`
- `story_generator`
- `script_segmenter`
- `character_designer`
- `video_assembler`

### List Checkpoints

```bash
python main.py --workflow-id my-video-001 --list-checkpoints
```

### Benefits

- **Cost Savings**: Avoid re-running expensive API calls after failures
- **Faster Iteration**: Restart from specific steps when tweaking later stages
- **Error Recovery**: Automatic recovery from interruptions
- **Debugging**: Inspect intermediate outputs at each step

For complete documentation, see [docs/checkpointing.md](docs/checkpointing.md).

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

> **📖 For detailed troubleshooting, see [TROUBLESHOOTING.md](TROUBLESHOOTING.md)**

### Common Issues

#### 1. ImageMagick Not Found (CRITICAL)

**Error:**
```
MoviePy Error: creation of None failed because of the following error:
[WinError 2] The system cannot find the file specified.
This error can be due to the fact that ImageMagick is not installed...
```

**Solution:**
1. Install ImageMagick from: https://imagemagick.org/script/download.php
2. During installation, check:
   - ✅ Install legacy utilities (e.g., convert)
   - ✅ Add application directory to your system path
3. Restart your terminal and verify: `magick -version`
4. If still not working, set `IMAGEMAGICK_BINARY` in your `.env` file

**Workaround:** Videos will be created without end cards if ImageMagick is unavailable.

#### 2. gTTS Narration Errors

**Error:**
```
Error generating gTTS narration: 200 (OK) from TTS API. Probable cause: Unknown
```

**Solutions:**
- **Option A:** Reinstall gTTS: `pip install --upgrade gtts`
- **Option B:** Use ElevenLabs instead (add `ELEVENLABS_API_KEY` to `.env`)
- **Option C:** Disable narration: Set `"narration": false` in preferences

**Causes:**
- Network/firewall blocking Google TTS service
- Rate limiting from Google
- Corrupted gTTS installation

#### 3. FFmpeg Not Found

**Error:**
```
ffmpeg: command not found
```

**Solution:**
- Ensure FFmpeg is installed and in PATH
- Test with: `ffmpeg -version`
- Windows: Add FFmpeg bin directory to system PATH
- Restart your terminal after installation

#### 4. OpenAI API Errors

**Common errors:**
- `Invalid API key`: Check your `.env` file
- `Insufficient quota`: Add credits to your OpenAI account
- `Rate limit exceeded`: Wait a few minutes and retry

**Solution:**
```bash
# Verify API key is set
echo $OPENAI_API_KEY  # macOS/Linux
echo $env:OPENAI_API_KEY  # Windows PowerShell
```

#### 5. Image Generation Fails

**Solutions:**
- Verify DALL-E 3 API access in your OpenAI account
- Check image generation rate limits (5 images/minute for free tier)
- Ensure sufficient API credits
- Use `--estimate-cost` to check costs before running

#### 6. Video Assembly Fails

**Checklist:**
- ✅ FFmpeg installed and in PATH
- ✅ ImageMagick installed (for end cards)
- ✅ Image files exist in `temp/images/`
- ✅ Sufficient disk space (at least 500MB free)
- ✅ No file permission issues

#### 7. Memory Issues

**Solutions:**
- Reduce number of scenes (shorter duration)
- Lower image resolution in `config.py`
- Close other applications
- Use a machine with more RAM (8GB+ recommended)

#### 8. Workflow Interrupted

**Recovery:**
```bash
# Resume from latest checkpoint
python main.py --workflow-id my-video-001 --resume

# List available checkpoints
python main.py --workflow-id my-video-001 --list-checkpoints

# Resume from specific step
python main.py --workflow-id my-video-001 --resume-from-step video_assembler
```

### Quick Diagnostics

Run these commands to check your setup:

```bash
# Check Python packages
pip list | grep -E "moviepy|gtts|langchain|openai"

# Check system binaries
ffmpeg -version
magick -version

# Check environment variables
echo $OPENAI_API_KEY  # Should not be empty
```

**Windows PowerShell:**
```powershell
pip list | Select-String "moviepy|gtts|langchain|openai"
ffmpeg -version
magick -version
Get-ChildItem Env: | Select-String "OPENAI|IMAGEMAGICK"
```

### Debug Mode

Run with debug logging for detailed error information:

```bash
python main.py -i story.json --log-level DEBUG --log-file debug.log
```

Check the log file for detailed error traces and API responses.

### Error Handling Features

The system includes comprehensive error handling:
- ✅ Automatic retries with exponential backoff
- ✅ Graceful degradation (e.g., skip web search if API fails)
- ✅ Clear error messages with actionable solutions
- ✅ State persistence for recovery via checkpoints
- ✅ Automatic ImageMagick path detection
- ✅ Fallback to gTTS if ElevenLabs fails

### Getting Help

If you're still experiencing issues:

1. Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for detailed solutions
2. Review logs in `debug.log` or console output
3. Verify all prerequisites are installed correctly
4. Try running with `--estimate-cost` first to validate setup
5. Open an issue on GitHub with:
   - Error message and full stack trace
   - Output of diagnostic commands above
   - Your OS and Python version

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

