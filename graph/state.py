"""State management for the moral video workflow using LangGraph."""

from typing import TypedDict, List, Optional, Dict, Any
from typing_extensions import Annotated
import operator


class MoralVideoState(TypedDict):
    """
    State schema for the moral video generation workflow.
    
    This TypedDict defines all the data that flows through the LangGraph workflow,
    tracking progress from input context to final video output.
    """
    
    # Input context and parameters
    input_context: Optional[Dict[str, Any]]  # Original input context
    input_preferences: Optional[Dict[str, Any]]  # User preferences (art style, narration, etc.)
    
    # Context analysis results
    validated_context: Optional[Dict[str, Any]]  # Validated and enriched context
    search_queries: Optional[List[str]]  # Generated search queries for research
    
    # Web research results
    research_results: Optional[Dict[str, Any]]  # Curated research summary
    research_summary: Optional[str]  # Text summary of research findings
    
    # Story generation results
    generated_story: Optional[str]  # Complete story text
    story_metadata: Optional[Dict[str, Any]]  # Story metadata (word count, themes, etc.)
    
    # Script segmentation results
    script_segments: Optional[List[Dict[str, Any]]]  # Array of scene objects
    # Each segment contains:
    #   - scene_number: int
    #   - description: str
    #   - characters: List[str]
    #   - dialogue: Optional[str]
    #   - narration: Optional[str]
    #   - duration_seconds: float
    #   - setting: str
    #   - emotions: List[str]
    
    # Character design results
    character_descriptions: Optional[Dict[str, Dict[str, Any]]]  # Character reference sheets
    # Format: {character_name: {description, traits, design_prompt, reference_image_url}}
    scene_images: Optional[List[str]]  # List of image file paths for each scene
    
    # Video assembly results
    video_segments: Optional[List[str]]  # Temporary video segment paths
    narration_audio: Optional[str]  # Path to narration audio file
    background_music: Optional[str]  # Path to background music file
    final_video_path: Optional[str]  # Path to final compiled video
    
    # Error handling and retry tracking
    errors: Annotated[List[Dict[str, Any]], operator.add]  # List of errors encountered
    # Each error contains:
    #   - agent: str (agent name)
    #   - error_type: str
    #   - error_message: str
    #   - timestamp: str
    #   - retry_count: int
    
    retry_counts: Optional[Dict[str, int]]  # Retry count per agent
    current_agent: Optional[str]  # Current agent being executed
    
    # Workflow metadata
    workflow_id: Optional[str]  # Unique workflow execution ID
    start_time: Optional[str]  # Workflow start timestamp
    progress: Optional[float]  # Progress percentage (0.0 to 1.0)
    status: Optional[str]  # "running", "completed", "failed", "paused"
    
    # Quality validation flags
    quality_checks: Optional[Dict[str, bool]]  # Quality check results
    # Keys: "story_quality", "image_quality", "video_quality", "age_appropriate"
    
    # Optional human approval checkpoints
    requires_approval: Optional[bool]  # Whether workflow is waiting for approval
    approval_status: Optional[str]  # "pending", "approved", "rejected"


def create_initial_state(
    input_context: Dict[str, Any],
    input_preferences: Dict[str, Any],
    workflow_id: Optional[str] = None
) -> MoralVideoState:
    """
    Create initial state for the workflow.
    
    Args:
        input_context: Input context dictionary with theme, characters, etc.
        input_preferences: User preferences for art style, narration, etc.
        workflow_id: Optional unique workflow ID
        
    Returns:
        MoralVideoState: Initialized state dictionary
    """
    from datetime import datetime
    import uuid
    
    if workflow_id is None:
        workflow_id = str(uuid.uuid4())
    
    return MoralVideoState(
        input_context=input_context,
        input_preferences=input_preferences,
        validated_context=None,
        search_queries=None,
        research_results=None,
        research_summary=None,
        generated_story=None,
        story_metadata=None,
        script_segments=None,
        character_descriptions=None,
        scene_images=None,
        video_segments=None,
        narration_audio=None,
        background_music=None,
        final_video_path=None,
        errors=[],
        retry_counts={},
        current_agent=None,
        workflow_id=workflow_id,
        start_time=datetime.now().isoformat(),
        progress=0.0,
        status="running",
        quality_checks={},
        requires_approval=False,
        approval_status=None,
    )


def update_progress(state: MoralVideoState, agent_name: str, progress_value: float) -> Dict[str, Any]:
    """
    Update progress in state.
    
    Args:
        state: Current state
        agent_name: Name of current agent
        progress_value: Progress value (0.0 to 1.0)
        
    Returns:
        Dict with updated progress fields
    """
    return {
        "current_agent": agent_name,
        "progress": min(max(progress_value, 0.0), 1.0),
    }


def add_error(
    state: MoralVideoState,
    agent_name: str,
    error_type: str,
    error_message: str,
    retry_count: int = 0
) -> Dict[str, Any]:
    """
    Add error to state.
    
    Args:
        state: Current state
        agent_name: Name of agent that encountered error
        error_type: Type of error
        error_message: Error message
        retry_count: Current retry count
        
    Returns:
        Dict with error information (for Annotated list append)
    """
    from datetime import datetime
    
    error_info = {
        "agent": agent_name,
        "error_type": error_type,
        "error_message": error_message,
        "timestamp": datetime.now().isoformat(),
        "retry_count": retry_count,
    }
    
    # Update retry counts
    retry_counts = state.get("retry_counts", {}) or {}
    retry_counts[agent_name] = retry_count
    
    return {
        "errors": [error_info],
        "retry_counts": retry_counts,
    }

