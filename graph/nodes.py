"""Node functions for LangGraph workflow."""

import logging
import time
import json
from typing import Dict, Any
from pathlib import Path

from graph.state import MoralVideoState, update_progress, add_error
from agents.context_analyzer import ContextAnalyzerAgent
from agents.web_researcher import WebResearchAgent
from agents.story_generator import StoryGeneratorAgent
from agents.script_segmenter import ScriptSegmentationAgent
from agents.character_designer import CharacterDesignAgent
from agents.video_assembler import VideoAssemblyAgent
from config import get_config
from utils.checkpoint_manager import save_checkpoint

logger = logging.getLogger(__name__)


def context_analyzer_node(state: MoralVideoState) -> Dict[str, Any]:
    """
    Context analyzer node.
    
    Args:
        state: Current workflow state
        
    Returns:
        Updated state dictionary
    """
    config = get_config()
    agent = ContextAnalyzerAgent()
    
    try:
        logger.info("Executing context analyzer node")
        
        # Check if output already exists in state (from checkpoint)
        if state.get("validated_context") and state.get("search_queries"):
            logger.info("Context analyzer output found in state, skipping execution")
            return {
                "current_agent": "context_analyzer",
                "progress": 0.1,
                "validated_context": state.get("validated_context"),
                "search_queries": state.get("search_queries"),
                "last_completed_step": "context_analyzer",
            }
        
        # Update progress
        progress_update = update_progress(state, "context_analyzer", 0.1)
        
        # Get input
        input_context = state.get("input_context", {})
        input_preferences = state.get("input_preferences", {})
        input_data = {
            "context": input_context,
            "preferences": input_preferences
        }
        
        # Analyze context
        validated_context = agent.analyze(input_data)
        
        # Extract search queries
        search_queries = validated_context.get("search_queries", [])
        
        # Prepare result
        result = {
            **progress_update,
            "validated_context": validated_context,
            "search_queries": search_queries,
            "last_completed_step": "context_analyzer",
        }
        
        # Save checkpoint if enabled
        if config.enable_auto_checkpoint:
            workflow_id = state.get("workflow_id", "default")
            workflow_checkpoint_dir = config.paths.checkpoint_dir / workflow_id
            workflow_checkpoint_dir.mkdir(parents=True, exist_ok=True)
            
            # Save intermediate outputs
            with open(workflow_checkpoint_dir / "01_validated_context.json", 'w') as f:
                json.dump(validated_context, f, indent=2)
            
            with open(workflow_checkpoint_dir / "01_search_queries.json", 'w') as f:
                json.dump(search_queries, f, indent=2)
            
            # Save checkpoint
            merged_state = {**state, **result}
            checkpoint_path = save_checkpoint(
                state=merged_state,
                step_name="context_analyzer",
                checkpoint_dir=config.paths.checkpoint_dir,
                workflow_id=workflow_id,
                retention_count=config.checkpoint_retention_count
            )
            result["checkpoint_path"] = str(checkpoint_path)
            logger.info(f"Checkpoint saved: {checkpoint_path}")
        
        return result
        
    except Exception as e:
        logger.error(f"Error in context analyzer node: {e}")
        error_update = add_error(state, "context_analyzer", "ContextAnalysisError", str(e), 0)
        return {
            **error_update,
            "status": "failed",
        }


def web_researcher_node(state: MoralVideoState) -> Dict[str, Any]:
    """
    Web researcher node.
    
    Args:
        state: Current workflow state
        
    Returns:
        Updated state dictionary
    """
    config = get_config()
    agent = WebResearchAgent()
    
    try:
        logger.info("Executing web researcher node")
        
        # Check if output already exists in state (from checkpoint)
        if state.get("research_results") is not None and state.get("research_summary") is not None:
            logger.info("Web researcher output found in state, skipping execution")
            return {
                "current_agent": "web_researcher",
                "progress": 0.2,
                "research_results": state.get("research_results"),
                "research_summary": state.get("research_summary"),
                "last_completed_step": "web_researcher",
            }
        
        # Update progress
        progress_update = update_progress(state, "web_researcher", 0.2)
        
        # Get validated context and search queries
        validated_context = state.get("validated_context", {})
        search_queries = state.get("search_queries", [])
        
        if not search_queries:
            logger.warning("No search queries provided, skipping web research")
            return {
                **progress_update,
                "research_results": {},
                "research_summary": "No research queries provided.",
            }
        
        # Execute research
        age_group = validated_context.get("age_group", "6-8")
        research_results = agent.research(
            context=validated_context,
            search_queries=search_queries,
            age_group=age_group
        )
        
        # Prepare result
        result = {
            **progress_update,
            "research_results": research_results.get("research_results", {}),
            "research_summary": research_results.get("research_summary", ""),
            "last_completed_step": "web_researcher",
        }
        
        # Save checkpoint if enabled
        if config.enable_auto_checkpoint:
            workflow_id = state.get("workflow_id", "default")
            workflow_checkpoint_dir = config.paths.checkpoint_dir / workflow_id
            workflow_checkpoint_dir.mkdir(parents=True, exist_ok=True)
            
            # Save intermediate outputs
            with open(workflow_checkpoint_dir / "02_research_results.json", 'w') as f:
                json.dump(result["research_results"], f, indent=2)
            
            with open(workflow_checkpoint_dir / "02_research_summary.txt", 'w') as f:
                f.write(result["research_summary"])
            
            # Save checkpoint
            merged_state = {**state, **result}
            checkpoint_path = save_checkpoint(
                state=merged_state,
                step_name="web_researcher",
                checkpoint_dir=config.paths.checkpoint_dir,
                workflow_id=workflow_id,
                retention_count=config.checkpoint_retention_count
            )
            result["checkpoint_path"] = str(checkpoint_path)
            logger.info(f"Checkpoint saved: {checkpoint_path}")
        
        return result
        
    except Exception as e:
        logger.error(f"Error in web researcher node: {e}")
        error_update = add_error(state, "web_researcher", "WebResearchError", str(e), 0)
        progress_update = update_progress(state, "web_researcher", 0.2)
        # Graceful degradation: continue without research
        return {
            **error_update,
            **progress_update,
            "research_results": {},
            "research_summary": "Research unavailable. Proceeding with context only.",
        }


def story_generator_node(state: MoralVideoState) -> Dict[str, Any]:
    """
    Story generator node.
    
    Args:
        state: Current workflow state
        
    Returns:
        Updated state dictionary
    """
    config = get_config()
    agent = StoryGeneratorAgent()
    
    try:
        logger.info("Executing story generator node")
        
        # Check if output already exists in state (from checkpoint)
        if state.get("generated_story") and state.get("story_metadata"):
            logger.info("Story generator output found in state, skipping execution")
            return {
                "current_agent": "story_generator",
                "progress": 0.35,
                "generated_story": state.get("generated_story"),
                "story_metadata": state.get("story_metadata"),
                "last_completed_step": "story_generator",
            }
        
        # Update progress
        progress_update = update_progress(state, "story_generator", 0.35)
        
        # Get validated context and research summary
        validated_context = state.get("validated_context", {})
        research_summary = state.get("research_summary", "")
        
        # Generate story
        story_result = agent.generate(
            context=validated_context,
            research_summary=research_summary
        )
        
        # Prepare result
        result = {
            **progress_update,
            "generated_story": story_result.get("story", ""),
            "story_metadata": story_result.get("metadata", {}),
            "last_completed_step": "story_generator",
        }
        
        # Save checkpoint if enabled
        if config.enable_auto_checkpoint:
            workflow_id = state.get("workflow_id", "default")
            workflow_checkpoint_dir = config.paths.checkpoint_dir / workflow_id
            workflow_checkpoint_dir.mkdir(parents=True, exist_ok=True)
            
            # Save intermediate outputs
            with open(workflow_checkpoint_dir / "03_story.txt", 'w', encoding='utf-8') as f:
                f.write(result["generated_story"])
            
            with open(workflow_checkpoint_dir / "03_story_metadata.json", 'w') as f:
                json.dump(result["story_metadata"], f, indent=2)
            
            # Save checkpoint
            merged_state = {**state, **result}
            checkpoint_path = save_checkpoint(
                state=merged_state,
                step_name="story_generator",
                checkpoint_dir=config.paths.checkpoint_dir,
                workflow_id=workflow_id,
                retention_count=config.checkpoint_retention_count
            )
            result["checkpoint_path"] = str(checkpoint_path)
            logger.info(f"Checkpoint saved: {checkpoint_path}")
        
        return result
        
    except Exception as e:
        logger.error(f"Error in story generator node: {e}")
        error_update = add_error(state, "story_generator", "StoryGenerationError", str(e), 0)
        return {
            **error_update,
            "status": "failed",
        }


def script_segmenter_node(state: MoralVideoState) -> Dict[str, Any]:
    """
    Script segmenter node.
    
    Args:
        state: Current workflow state
        
    Returns:
        Updated state dictionary
    """
    config = get_config()
    agent = ScriptSegmentationAgent()
    
    try:
        logger.info("Executing script segmenter node")
        
        # Check if output already exists in state (from checkpoint)
        if state.get("script_segments"):
            logger.info("Script segmenter output found in state, skipping execution")
            return {
                "current_agent": "script_segmenter",
                "progress": 0.5,
                "script_segments": state.get("script_segments"),
                "last_completed_step": "script_segmenter",
            }
        
        # Update progress
        progress_update = update_progress(state, "script_segmenter", 0.5)
        
        # Get story and context
        story = state.get("generated_story", "")
        validated_context = state.get("validated_context", {})
        target_duration = validated_context.get("duration_minutes", 3)
        
        if not story:
            raise ValueError("No story generated")
        
        # Segment story
        segments = agent.segment(
            story=story,
            context=validated_context,
            target_duration_minutes=target_duration
        )
        
        # Prepare result
        result = {
            **progress_update,
            "script_segments": segments,
            "last_completed_step": "script_segmenter",
        }
        
        # Save checkpoint if enabled
        if config.enable_auto_checkpoint:
            workflow_id = state.get("workflow_id", "default")
            workflow_checkpoint_dir = config.paths.checkpoint_dir / workflow_id
            workflow_checkpoint_dir.mkdir(parents=True, exist_ok=True)
            
            # Save intermediate outputs
            with open(workflow_checkpoint_dir / "04_script_segments.json", 'w') as f:
                json.dump(segments, f, indent=2)
            
            # Save checkpoint
            merged_state = {**state, **result}
            checkpoint_path = save_checkpoint(
                state=merged_state,
                step_name="script_segmenter",
                checkpoint_dir=config.paths.checkpoint_dir,
                workflow_id=workflow_id,
                retention_count=config.checkpoint_retention_count
            )
            result["checkpoint_path"] = str(checkpoint_path)
            logger.info(f"Checkpoint saved: {checkpoint_path}")
        
        return result
        
    except Exception as e:
        logger.error(f"Error in script segmenter node: {e}")
        error_update = add_error(state, "script_segmenter", "ScriptSegmentationError", str(e), 0)
        return {
            **error_update,
            "status": "failed",
        }


def character_designer_node(state: MoralVideoState) -> Dict[str, Any]:
    """
    Character designer node.
    
    Args:
        state: Current workflow state
        
    Returns:
        Updated state dictionary
    """
    config = get_config()
    agent = CharacterDesignAgent()
    
    try:
        logger.info("Executing character designer node")
        
        # Check if output already exists in state (from checkpoint)
        if state.get("character_descriptions") and state.get("scene_images"):
            logger.info("Character designer output found in state, skipping execution")
            return {
                "current_agent": "character_designer",
                "progress": 0.65,
                "character_descriptions": state.get("character_descriptions"),
                "scene_images": state.get("scene_images"),
                "last_completed_step": "character_designer",
            }
        
        # Update progress
        progress_update = update_progress(state, "character_designer", 0.65)
        
        # Get context and preferences
        validated_context = state.get("validated_context", {})
        input_preferences = state.get("input_preferences", {})
        art_style = input_preferences.get("art_style", "cartoon")
        
        # Design characters
        character_descriptions = agent.design_characters(
            context=validated_context,
            art_style=art_style
        )
        
        # Get script segments
        script_segments = state.get("script_segments", [])
        
        if not script_segments:
            raise ValueError("No script segments available")
        
        # Generate scene images
        scene_images = agent.generate_scene_images(
            script_segments=script_segments,
            character_descriptions=character_descriptions,
            context=validated_context,
            art_style=art_style
        )
        
        # Convert Path objects to strings for state
        scene_images_str = [str(img) if img else None for img in scene_images]
        
        # Prepare result
        result = {
            **progress_update,
            "character_descriptions": character_descriptions,
            "scene_images": scene_images_str,
            "last_completed_step": "character_designer",
        }
        
        # Save checkpoint if enabled
        if config.enable_auto_checkpoint:
            workflow_id = state.get("workflow_id", "default")
            workflow_checkpoint_dir = config.paths.checkpoint_dir / workflow_id
            workflow_checkpoint_dir.mkdir(parents=True, exist_ok=True)
            
            # Save intermediate outputs
            with open(workflow_checkpoint_dir / "05_character_descriptions.json", 'w') as f:
                json.dump(character_descriptions, f, indent=2)
            
            # Scene images are already saved to temp/images, just document paths
            with open(workflow_checkpoint_dir / "05_scene_image_paths.json", 'w') as f:
                json.dump(scene_images_str, f, indent=2)
            
            # Save checkpoint
            merged_state = {**state, **result}
            checkpoint_path = save_checkpoint(
                state=merged_state,
                step_name="character_designer",
                checkpoint_dir=config.paths.checkpoint_dir,
                workflow_id=workflow_id,
                retention_count=config.checkpoint_retention_count
            )
            result["checkpoint_path"] = str(checkpoint_path)
            logger.info(f"Checkpoint saved: {checkpoint_path}")
        
        return result
        
    except Exception as e:
        logger.error(f"Error in character designer node: {e}")
        error_update = add_error(state, "character_designer", "CharacterDesignError", str(e), 0)
        return {
            **error_update,
            "status": "failed",
        }


def video_assembler_node(state: MoralVideoState) -> Dict[str, Any]:
    """
    Video assembler node.
    
    Args:
        state: Current workflow state
        
    Returns:
        Updated state dictionary
    """
    config = get_config()
    agent = VideoAssemblyAgent()
    
    try:
        logger.info("Executing video assembler node")
        
        # Check if output already exists in state (from checkpoint)
        if state.get("final_video_path") and state.get("status") == "completed":
            logger.info("Video assembler output found in state, skipping execution")
            return {
                "current_agent": "video_assembler",
                "progress": 1.0,
                "final_video_path": state.get("final_video_path"),
                "status": "completed",
                "last_completed_step": "video_assembler",
            }
        
        # Update progress
        progress_update = update_progress(state, "video_assembler", 0.9)
        
        # Get all required data
        scene_images = state.get("scene_images", [])
        script_segments = state.get("script_segments", [])
        story = state.get("generated_story", "")
        validated_context = state.get("validated_context", {})
        character_descriptions = state.get("character_descriptions", {})
        workflow_id = state.get("workflow_id", "")
        
        # Combine context and preferences
        input_context = state.get("input_context", {})
        input_preferences = state.get("input_preferences", {})
        full_context = {
            **validated_context,
            "preferences": input_preferences,
            "moral_lesson": validated_context.get("moral_lesson", ""),
        }
        
        # Convert image paths to Path objects
        scene_image_paths = [Path(img) for img in scene_images if img]
        
        if not scene_image_paths:
            raise ValueError("No scene images available")
        
        # Assemble video
        final_video_path = agent.assemble_video(
            scene_images=scene_image_paths,
            script_segments=script_segments,
            story=story,
            context=full_context,
            character_descriptions=character_descriptions,
            workflow_id=workflow_id
        )
        
        if not final_video_path:
            raise ValueError("Failed to assemble video")
        
        # Prepare result
        result = {
            **progress_update,
            "final_video_path": str(final_video_path),
            "status": "completed",
            "progress": 1.0,
            "last_completed_step": "video_assembler",
        }
        
        # Save checkpoint if enabled
        if config.enable_auto_checkpoint:
            workflow_id_str = state.get("workflow_id", "default")
            workflow_checkpoint_dir = config.paths.checkpoint_dir / workflow_id_str
            workflow_checkpoint_dir.mkdir(parents=True, exist_ok=True)
            
            # Document final video path and any audio paths
            output_info = {
                "final_video_path": str(final_video_path),
                "narration_audio": state.get("narration_audio"),
                "background_music": state.get("background_music"),
            }
            
            with open(workflow_checkpoint_dir / "06_final_output.json", 'w') as f:
                json.dump(output_info, f, indent=2)
            
            # Save final checkpoint
            merged_state = {**state, **result}
            checkpoint_path = save_checkpoint(
                state=merged_state,
                step_name="video_assembler",
                checkpoint_dir=config.paths.checkpoint_dir,
                workflow_id=workflow_id_str,
                retention_count=config.checkpoint_retention_count
            )
            result["checkpoint_path"] = str(checkpoint_path)
            logger.info(f"Final checkpoint saved: {checkpoint_path}")
        
        return result
        
    except Exception as e:
        logger.error(f"Error in video assembler node: {e}")
        error_update = add_error(state, "video_assembler", "VideoAssemblyError", str(e), 0)
        return {
            **error_update,
            "status": "failed",
        }


def should_retry(state: MoralVideoState) -> str:
    """
    Determine if workflow should retry after error.
    
    Args:
        state: Current workflow state
        
    Returns:
        "retry" or "fail"
    """
    errors = state.get("errors", [])
    if not errors:
        return "continue"
    
    # Get last error
    last_error = errors[-1]
    agent_name = last_error.get("agent", "")
    retry_count = last_error.get("retry_count", 0)
    
    # Check retry count
    max_retries = get_config().retry.max_retries
    if retry_count >= max_retries:
        logger.error(f"Max retries exceeded for {agent_name}")
        return "fail"
    
    return "retry"


def check_quality(state: MoralVideoState) -> str:
    """
    Check quality validation checkpoints.
    
    Args:
        state: Current workflow state
        
    Returns:
        "continue" or "fail"
    """
    quality_checks = state.get("quality_checks", {})
    
    # Check if all quality checks passed
    if quality_checks:
        failed_checks = [k for k, v in quality_checks.items() if not v]
        if failed_checks:
            logger.warning(f"Quality checks failed: {failed_checks}")
            # Continue anyway, but log warning
    
    return "continue"

