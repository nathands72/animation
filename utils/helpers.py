"""Helper functions for logging, file management, and cost estimation."""

import logging
import sys
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
import json

from config import get_config


def setup_logging(log_level: str = "INFO", log_file: Optional[str] = None) -> logging.Logger:
    """
    Set up structured logging for the application.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional path to log file
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger("moral_video_workflow")
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Remove existing handlers
    logger.handlers = []
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler with UTF-8 encoding
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    # Set UTF-8 encoding for console output
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    logger.addHandler(console_handler)
    
    # File handler if specified with UTF-8 encoding
    if log_file:
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


def get_output_path(filename: str, subdirectory: Optional[str] = None) -> Path:
    """
    Get output path for a file.
    
    Args:
        filename: Name of the file
        subdirectory: Optional subdirectory within output directory
        
    Returns:
        Path object for the output file
    """
    config = get_config()
    output_dir = config.paths.output_dir
    
    if subdirectory:
        output_dir = output_dir / subdirectory
        output_dir.mkdir(parents=True, exist_ok=True)
    
    return output_dir / filename


def get_temp_path(filename: str, subdirectory: Optional[str] = None) -> Path:
    """
    Get temporary path for a file.
    
    Args:
        filename: Name of the file
        subdirectory: Optional subdirectory within temp directory
        
    Returns:
        Path object for the temp file
    """
    config = get_config()
    temp_dir = config.paths.temp_dir
    
    if subdirectory:
        temp_dir = temp_dir / subdirectory
        temp_dir.mkdir(parents=True, exist_ok=True)
    
    return temp_dir / filename


def estimate_cost(
    num_images: int = 0,
    num_tokens: int = 0,
    num_searches: int = 0,
    use_tts: bool = False
) -> Dict[str, float]:
    """
    Estimate cost for workflow execution.
    
    Args:
        num_images: Number of images to generate
        num_tokens: Estimated number of LLM tokens
        num_searches: Number of web searches
        use_tts: Whether text-to-speech will be used
        
    Returns:
        Dictionary with cost breakdown
    """
    # Pricing (as of 2024, adjust as needed)
    COSTS = {
        "gpt4_input": 0.03 / 1000,  # $0.03 per 1K tokens
        "gpt4_output": 0.06 / 1000,  # $0.06 per 1K tokens
        "dalle3_standard": 0.040,  # $0.040 per image
        "dalle3_hd": 0.080,  # $0.080 per image
        "tavily_search": 0.001,  # $0.001 per search (approximate)
        "gtts": 0.0,  # Free
        "elevenlabs": 0.30,  # $0.30 per 1000 characters (approximate)
    }
    
    config = get_config()
    
    # Estimate token costs (assuming 70% input, 30% output)
    input_tokens = int(num_tokens * 0.7)
    output_tokens = int(num_tokens * 0.3)
    token_cost = (input_tokens * COSTS["gpt4_input"]) + (output_tokens * COSTS["gpt4_output"])
    
    # Image generation costs
    image_cost = 0.0
    if num_images > 0:
        if config.image_gen.quality == "hd":
            image_cost = num_images * COSTS["dalle3_hd"]
        else:
            image_cost = num_images * COSTS["dalle3_standard"]
    
    # Search costs
    search_cost = num_searches * COSTS["tavily_search"]
    
    # TTS costs
    tts_cost = 0.0
    if use_tts:
        if config.tts.provider == "elevenlabs":
            # Estimate 1000 characters per minute of narration
            estimated_chars = 1000  # Rough estimate
            tts_cost = (estimated_chars / 1000) * COSTS["elevenlabs"]
        else:
            tts_cost = COSTS["gtts"]
    
    total_cost = token_cost + image_cost + search_cost + tts_cost
    
    return {
        "llm_tokens": token_cost,
        "image_generation": image_cost,
        "web_search": search_cost,
        "text_to_speech": tts_cost,
        "total": total_cost,
    }


def save_state_checkpoint(state: Dict[str, Any], checkpoint_path: Path) -> None:
    """
    Save workflow state to a checkpoint file.
    
    Args:
        state: State dictionary to save
        checkpoint_path: Path to save checkpoint
    """
    # Convert Path objects to strings for JSON serialization
    serializable_state = {}
    for key, value in state.items():
        if isinstance(value, Path):
            serializable_state[key] = str(value)
        elif isinstance(value, dict):
            serializable_state[key] = {
                k: str(v) if isinstance(v, Path) else v
                for k, v in value.items()
            }
        elif isinstance(value, list):
            serializable_state[key] = [
                str(item) if isinstance(item, Path) else item
                for item in value
            ]
        else:
            serializable_state[key] = value
    
    checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
    with open(checkpoint_path, "w") as f:
        json.dump(serializable_state, f, indent=2, default=str)


def load_state_checkpoint(checkpoint_path: Path) -> Optional[Dict[str, Any]]:
    """
    Load workflow state from a checkpoint file.
    
    Args:
        checkpoint_path: Path to checkpoint file
        
    Returns:
        State dictionary or None if file doesn't exist
    """
    if not checkpoint_path.exists():
        return None
    
    try:
        with open(checkpoint_path, "r") as f:
            return json.load(f)
    except Exception as e:
        logging.getLogger("moral_video_workflow").error(f"Error loading checkpoint: {e}")
        return None


def format_duration(seconds: float) -> str:
    """
    Format duration in seconds to human-readable string.
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        Formatted duration string (e.g., "2m 30s")
    """
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    
    if minutes > 0:
        return f"{minutes}m {secs}s"
    else:
        return f"{secs}s"


def clean_temp_files(workflow_id: Optional[str] = None) -> None:
    """
    Clean up temporary files.
    
    Args:
        workflow_id: Optional workflow ID to clean specific files
    """
    config = get_config()
    temp_dir = config.paths.temp_dir
    
    if workflow_id:
        # Clean specific workflow files
        pattern = f"*{workflow_id}*"
        for path in temp_dir.rglob(pattern):
            if path.is_file():
                path.unlink()
    else:
        # Clean all temp files older than 24 hours
        from datetime import timedelta
        cutoff_time = datetime.now() - timedelta(hours=24)
        
        for path in temp_dir.rglob("*"):
            if path.is_file():
                try:
                    mtime = datetime.fromtimestamp(path.stat().st_mtime)
                    if mtime < cutoff_time:
                        path.unlink()
                except Exception:
                    pass  # Skip files that can't be deleted


def sanitize_text(text: str) -> str:
    """
    Sanitize text by replacing problematic Unicode characters with ASCII equivalents.
    
    Args:
        text: Text to sanitize
        
    Returns:
        Sanitized text safe for Windows console/file output
    """
    if not isinstance(text, str):
        return str(text)
    
    # Replace common problematic Unicode characters
    replacements = {
        '\u2192': '->',   # Right arrow
        '\u2190': '<-',   # Left arrow
        '\u2194': '<->', # Left-right arrow
        '\u2022': '*',    # Bullet point
        '\u2013': '-',    # En dash
        '\u2014': '--',   # Em dash
        '\u201c': '"',    # Left double quote
        '\u201d': '"',    # Right double quote
        '\u2018': "'",    # Left single quote
        '\u2019': "'",    # Right single quote
        '\u2026': '...', # Horizontal ellipsis
    }
    
    for unicode_char, replacement in replacements.items():
        text = text.replace(unicode_char, replacement)
    
    # Handle any remaining non-ASCII characters
    try:
        text.encode('ascii')
    except UnicodeEncodeError:
        # Replace remaining problematic characters
        text = text.encode('ascii', errors='replace').decode('ascii')
    
    return text
