"""Configuration management for the moral video workflow system."""

import os
from typing import Optional
from dataclasses import dataclass, field
from pathlib import Path

@dataclass
class LLMConfig:
    """LLM configuration settings."""
    
    provider: str = "openai"
    model: str = "gpt-4-turbo"
    temperature: float = 0.7
    max_tokens: int = 12000
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    
    def __post_init__(self):
        """Load API key and base URL from environment if not provided."""
        if self.api_key is None:
            self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        
        if self.base_url is None:
            self.base_url = os.getenv("OPENAI_BASE_URL")


@dataclass
class SearchConfig:
    """Web search API configuration."""
    
    provider: str = "tavily"  # or "serpapi"
    api_key: Optional[str] = None
    max_results: int = 5
    enable_child_safety_filter: bool = True
    
    def __post_init__(self):
        """Load API key from environment if not provided."""
        if self.api_key is None:
            if self.provider == "tavily":
                self.api_key = os.getenv("TAVILY_API_KEY")
            elif self.provider == "serpapi":
                self.api_key = os.getenv("SERPAPI_API_KEY")
        
        # Search can work without API key (graceful degradation)
        if not self.api_key:
            print("Warning: Search API key not found. Web research will be skipped.")


@dataclass
class ImageGenConfig:
    """Image generation API configuration."""
    
    provider: str = "dalle3"  # or "stable-diffusion", "midjourney"
    api_key: Optional[str] = None
    model: str = "dall-e-3"
    size: str = "1024x1024"  # Will be resized to 1920x1080
    quality: str = "standard"
    style: str = "vivid"
    
    def __post_init__(self):
        """Load API key from environment if not provided."""
        if self.api_key is None:
            if self.provider == "dalle3":
                self.api_key = os.getenv("OPENAI_API_KEY")
            elif self.provider == "stable-diffusion":
                self.api_key = os.getenv("STABLE_DIFFUSION_API_KEY")
            elif self.provider == "midjourney":
                self.api_key = os.getenv("MIDJOURNEY_API_KEY")
        
        if not self.api_key and self.provider == "dalle3":
            # Try to use OpenAI key from LLM config
            pass


@dataclass
class TTSConfig:
    """Text-to-speech configuration."""
    
    provider: str = "gtts"  # or "elevenlabs"
    api_key: Optional[str] = None
    voice_id: Optional[str] = None
    language: str = "en"
    speed: float = 1.0
    
    def __post_init__(self):
        """Load API key from environment if not provided."""
        if self.provider == "elevenlabs" and self.api_key is None:
            self.api_key = os.getenv("ELEVENLABS_API_KEY")
            if not self.api_key:
                print("Warning: ElevenLabs API key not found. Falling back to gTTS.")


@dataclass
class VideoConfig:
    """Video processing configuration."""
    
    output_resolution: str = "1080p"  # or "720p"
    fps: int = 24
    transition_duration: float = 0.5  # seconds
    background_music: bool = True
    music_volume: float = 0.3  # 0.0 to 1.0


@dataclass
class RetryConfig:
    """Retry and error handling configuration."""
    
    max_retries: int = 3
    initial_backoff: float = 1.0  # seconds
    max_backoff: float = 60.0  # seconds
    exponential_base: float = 2.0


@dataclass
class PathConfig:
    """Path configuration for outputs and temporary files."""
    
    output_dir: Path = field(default_factory=lambda: Path("output"))
    temp_dir: Path = field(default_factory=lambda: Path("temp"))
    images_dir: Path = field(default_factory=lambda: Path("temp/images"))
    audio_dir: Path = field(default_factory=lambda: Path("temp/audio"))
    checkpoint_dir: Path = field(default_factory=lambda: Path("temp/checkpoints"))
    
    def __post_init__(self):
        """Create directories if they don't exist."""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        self.images_dir.mkdir(parents=True, exist_ok=True)
        self.audio_dir.mkdir(parents=True, exist_ok=True)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)


@dataclass
class WorkflowConfig:
    """Main workflow configuration."""
    
    llm: LLMConfig = field(default_factory=LLMConfig)
    search: SearchConfig = field(default_factory=SearchConfig)
    image_gen: ImageGenConfig = field(default_factory=ImageGenConfig)
    tts: TTSConfig = field(default_factory=TTSConfig)
    video: VideoConfig = field(default_factory=VideoConfig)
    retry: RetryConfig = field(default_factory=RetryConfig)
    paths: PathConfig = field(default_factory=PathConfig)
    
    # Workflow settings
    enable_checkpointing: bool = True
    enable_progress_callbacks: bool = True
    max_workflow_duration: int = 600  # 10 minutes in seconds
    enable_human_approval: bool = False  # Optional human-in-the-loop
    
    # Checkpoint settings
    enable_auto_checkpoint: bool = True  # Automatically save checkpoints after each step
    checkpoint_retention_count: int = 10  # Number of checkpoints to retain per workflow
    
    def __post_init__(self):
        """Post-initialization setup."""
        # Share OpenAI API key between LLM and DALL-E if using same provider
        if self.image_gen.provider == "dalle3" and self.llm.provider == "openai" and not self.image_gen.api_key:
            self.image_gen.api_key = self.llm.api_key


def load_config() -> WorkflowConfig:
    """
    Load configuration from environment variables.
    
    Returns:
        WorkflowConfig: Configured workflow settings
    """
    return WorkflowConfig()


# Global config instance
_config: Optional[WorkflowConfig] = None


def get_config() -> WorkflowConfig:
    """
    Get or create global configuration instance.
    
    Returns:
        WorkflowConfig: Global configuration instance
    """
    global _config
    if _config is None:
        _config = load_config()
    return _config


def reset_config():
    """Reset global configuration (useful for testing)."""
    global _config
    _config = None

