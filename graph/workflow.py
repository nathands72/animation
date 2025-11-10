"""LangGraph workflow for moral video generation."""

import logging
from typing import Dict, Any, Optional

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from graph.state import MoralVideoState, create_initial_state
from graph.nodes import (
    context_analyzer_node,
    web_researcher_node,
    story_generator_node,
    script_segmenter_node,
    character_designer_node,
    video_assembler_node,
    should_retry,
    check_quality,
)
from config import get_config

logger = logging.getLogger(__name__)


def create_workflow() -> StateGraph:
    """
    Create and compile the LangGraph workflow.
    
    Returns:
        Compiled StateGraph workflow
    """
    logger.info("Creating LangGraph workflow")
    
    # Create graph
    workflow = StateGraph(MoralVideoState)
    
    # Add nodes
    workflow.add_node("context_analyzer", context_analyzer_node)
    workflow.add_node("web_researcher", web_researcher_node)
    workflow.add_node("story_generator", story_generator_node)
    workflow.add_node("script_segmenter", script_segmenter_node)
    workflow.add_node("character_designer", character_designer_node)
    workflow.add_node("video_assembler", video_assembler_node)
    
    # Define edges
    workflow.set_entry_point("context_analyzer")
    
    # Linear flow with error handling
    workflow.add_edge("context_analyzer", "web_researcher")
    workflow.add_edge("web_researcher", "story_generator")
    workflow.add_edge("story_generator", "script_segmenter")
    workflow.add_edge("script_segmenter", "character_designer")
    workflow.add_edge("character_designer", "video_assembler")
    workflow.add_edge("video_assembler", END)
    
    # Compile graph
    config = get_config()
    
    # Add checkpointing if enabled
    if config.enable_checkpointing:
        checkpointer = MemorySaver()
        compiled_workflow = workflow.compile(checkpointer=checkpointer)
    else:
        compiled_workflow = workflow.compile()
    
    logger.info("Workflow created and compiled successfully")
    
    return compiled_workflow


def run_workflow(
    input_context: Dict[str, Any],
    input_preferences: Dict[str, Any],
    workflow_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Run the workflow with given input.
    
    Args:
        input_context: Input context dictionary
        input_preferences: Input preferences dictionary
        workflow_id: Optional workflow ID
        
    Returns:
        Final state dictionary
    """
    logger.info("Starting workflow execution")
    
    # Create workflow
    workflow = create_workflow()
    
    # Create initial state
    initial_state = create_initial_state(
        input_context=input_context,
        input_preferences=input_preferences,
        workflow_id=workflow_id
    )
    
    # Run workflow
    config = get_config()
    
    if config.enable_checkpointing:
        # Run with checkpointing
        config_dict = {"configurable": {"thread_id": workflow_id or "default"}}
        final_state = None
        
        for output in workflow.stream(initial_state, config=config_dict):
            # Extract state from output (output is a dict with node names as keys)
            node_name = list(output.keys())[0] if output else "unknown"
            node_state = output[node_name] if output and node_name in output else output
            
            # Log progress
            current_agent = node_state.get("current_agent", "unknown") if isinstance(node_state, dict) else "unknown"
            progress = node_state.get("progress", 0.0) if isinstance(node_state, dict) else 0.0
            logger.info(f"Progress: {progress:.1%} - Node: {node_name} - Current agent: {current_agent}")
            
            # Check for errors
            if isinstance(node_state, dict):
                errors = node_state.get("errors", [])
                if errors:
                    last_error = errors[-1]
                    logger.warning(f"Error in {last_error.get('agent', 'unknown')}: {last_error.get('error_message', '')}")
                
                # Update final state
                final_state = node_state
        
        return final_state if final_state else initial_state
    else:
        # Run without checkpointing
        final_state = workflow.invoke(initial_state)
        return final_state


def run_workflow_with_callbacks(
    input_context: Dict[str, Any],
    input_preferences: Dict[str, Any],
    progress_callback: Optional[callable] = None,
    workflow_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Run workflow with progress callbacks.
    
    Args:
        input_context: Input context dictionary
        input_preferences: Input preferences dictionary
        progress_callback: Optional callback function(state) -> None
        workflow_id: Optional workflow ID
        
    Returns:
        Final state dictionary
    """
    logger.info("Starting workflow execution with callbacks")
    
    # Create workflow
    workflow = create_workflow()
    
    # Create initial state
    initial_state = create_initial_state(
        input_context=input_context,
        input_preferences=input_preferences,
        workflow_id=workflow_id
    )
    
    # Run workflow with callbacks
    config = get_config()
    config_dict = {"configurable": {"thread_id": workflow_id or "default"}}
    
    final_state = None
    
    for output in workflow.stream(initial_state, config=config_dict):
        # Extract state from output (output is a dict with node names as keys)
        node_name = list(output.keys())[0] if output else "unknown"
        node_state = output[node_name] if output and node_name in output else output
        
        # Call progress callback if provided
        if progress_callback and isinstance(node_state, dict):
            try:
                progress_callback(node_state)
            except Exception as e:
                logger.warning(f"Error in progress callback: {e}")
        
        # Log progress
        if isinstance(node_state, dict):
            current_agent = node_state.get("current_agent", "unknown")
            progress = node_state.get("progress", 0.0)
            logger.info(f"Progress: {progress:.1%} - Node: {node_name} - Current agent: {current_agent}")
            
            # Check for errors
            errors = node_state.get("errors", [])
            if errors:
                last_error = errors[-1]
                logger.warning(f"Error in {last_error.get('agent', 'unknown')}: {last_error.get('error_message', '')}")
            
            # Update final state
            final_state = node_state
    
    return final_state if final_state else initial_state

