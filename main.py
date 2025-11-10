"""Main entry point for the moral video workflow system."""

import argparse
import json
import sys
import logging
from pathlib import Path
from typing import Dict, Any, Optional

from graph.workflow import run_workflow_with_callbacks
from graph.state import create_initial_state
from utils.validators import validate_input
from utils.helpers import setup_logging, get_output_path, estimate_cost, format_duration
from config import get_config
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


def load_input_from_file(file_path: str) -> Dict[str, Any]:
    """
    Load input context from JSON file.
    
    Args:
        file_path: Path to JSON file
        
    Returns:
        Input dictionary
    """
    try:
        with open(file_path, "r") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading input file: {e}")
        raise


def progress_callback(state: Dict[str, Any]):
    """
    Progress callback for workflow execution.
    
    Args:
        state: Current workflow state
    """
    current_agent = state.get("current_agent", "unknown")
    progress = state.get("progress", 0.0)
    status = state.get("status", "running")
    
    print(f"\rProgress: {progress:.1%} - {current_agent} - Status: {status}", end="", flush=True)
    
    # Check for errors
    errors = state.get("errors", [])
    if errors:
        last_error = errors[-1]
        print(f"\nWarning: Error in {last_error.get('agent', 'unknown')}: {last_error.get('error_message', '')}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Generate animated moral story videos for children using AI agents"
    )
    
    parser.add_argument(
        "--input",
        "-i",
        type=str,
        help="Path to input JSON file with context and preferences"
    )
    
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        help="Output directory for generated video (default: output/)"
    )
    
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level (default: INFO)"
    )
    
    parser.add_argument(
        "--log-file",
        type=str,
        help="Path to log file (optional)"
    )
    
    parser.add_argument(
        "--workflow-id",
        type=str,
        help="Optional workflow ID for tracking"
    )
    
    parser.add_argument(
        "--estimate-cost",
        action="store_true",
        help="Estimate cost before execution"
    )
    
    args = parser.parse_args()
    
    # Setup logging
    logger = setup_logging(log_level=args.log_level, log_file=args.log_file)
    
    # Load input
    if args.input:
        try:
            input_data = load_input_from_file(args.input)
        except Exception as e:
            logger.error(f"Failed to load input file: {e}")
            sys.exit(1)
    else:
        # Use example input
        logger.info("No input file provided, using example input")
        input_data = {
            "context": {
                "theme": "honesty",
                "characters": [
                    {"name": "Leo", "type": "animal", "traits": ["brave", "curious"]},
                    {"name": "Mia", "type": "animal", "traits": ["wise", "kind"]}
                ],
                "setting": "magical forest",
                "moral_lesson": "Honesty is the best policy, even when it's hard",
                "age_group": "6-8",
                "duration_minutes": 3
            },
            "preferences": {
                "art_style": "cartoon",
                "narration": True,
                "music": True
            }
        }
    
    # Validate input
    is_valid, error_message = validate_input(input_data)
    if not is_valid:
        logger.error(f"Input validation failed: {error_message}")
        sys.exit(1)
    
    # Estimate cost if requested
    if args.estimate_cost:
        logger.info("Estimating cost...")
        context = input_data.get("context", {})
        duration_minutes = context.get("duration_minutes", 3)
        
        # Estimate number of images (8-12 scenes)
        num_images = 10
        # Estimate tokens (rough estimate)
        num_tokens = 5000
        # Estimate searches
        num_searches = 5
        # TTS
        use_tts = input_data.get("preferences", {}).get("narration", True)
        
        cost_estimate = estimate_cost(
            num_images=num_images,
            num_tokens=num_tokens,
            num_searches=num_searches,
            use_tts=use_tts
        )
        
        print("\nCost Estimate:")
        print(f"  LLM Tokens: ${cost_estimate['llm_tokens']:.2f}")
        print(f"  Image Generation: ${cost_estimate['image_generation']:.2f}")
        print(f"  Web Search: ${cost_estimate['web_search']:.2f}")
        print(f"  Text-to-Speech: ${cost_estimate['text_to_speech']:.2f}")
        print(f"  Total: ${cost_estimate['total']:.2f}")
        print()
        
        response = input("Continue with execution? (y/n): ")
        if response.lower() != "y":
            logger.info("Execution cancelled by user")
            sys.exit(0)
    
    # Set output directory if specified
    if args.output:
        config = get_config()
        config.paths.output_dir = Path(args.output)
        config.paths.output_dir.mkdir(parents=True, exist_ok=True)
    
    # Extract context and preferences
    input_context = input_data.get("context", {})
    input_preferences = input_data.get("preferences", {})
    
    # Run workflow
    logger.info("Starting workflow execution")
    print("\n" + "="*60)
    print("Moral Video Workflow System")
    print("="*60 + "\n")
    
    try:
        final_state = run_workflow_with_callbacks(
            input_context=input_context,
            input_preferences=input_preferences,
            progress_callback=progress_callback,
            workflow_id=args.workflow_id
        )
        
        print("\n")  # New line after progress updates
        
        # Check final status
        status = final_state.get("status", "unknown")
        
        if status == "completed":
            final_video_path = final_state.get("final_video_path", "")
            
            if final_video_path:
                logger.info(f"Workflow completed successfully!")
                print("\n" + "="*60)
                print("Workflow Completed Successfully!")
                print("="*60)
                print(f"\nFinal video: {final_video_path}")
                
                # Print metadata
                story_metadata = final_state.get("story_metadata", {})
                if story_metadata:
                    print(f"\nStory Metadata:")
                    print(f"  Word count: {story_metadata.get('word_count', 'N/A')}")
                    print(f"  Estimated reading time: {story_metadata.get('estimated_reading_time_minutes', 0):.1f} minutes")
                
                script_segments = final_state.get("script_segments", [])
                if script_segments:
                    total_duration = sum(seg.get("duration_seconds", 0) for seg in script_segments)
                    print(f"  Video duration: {format_duration(total_duration)}")
                
                print()
            else:
                logger.error("Workflow completed but no video path found")
                sys.exit(1)
        else:
            logger.error(f"Workflow failed with status: {status}")
            
            # Print errors
            errors = final_state.get("errors", [])
            if errors:
                print("\nErrors encountered:")
                for error in errors:
                    print(f"  - {error.get('agent', 'unknown')}: {error.get('error_message', '')}")
            
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("Workflow interrupted by user")
        print("\n\nWorkflow interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Workflow execution failed: {e}", exc_info=True)
        print(f"\n\nWorkflow execution failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

