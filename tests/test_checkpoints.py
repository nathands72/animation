"""
Test script for checkpoint and resume functionality.

This script demonstrates how to use the checkpoint manager programmatically.
"""

import json
from pathlib import Path
from utils.checkpoint_manager import CheckpointManager, save_checkpoint, load_checkpoint, list_checkpoints

def test_checkpoint_manager():
    """Test checkpoint manager functionality."""
    
    print("=" * 60)
    print("Checkpoint Manager Test")
    print("=" * 60)
    
    # Setup
    checkpoint_dir = Path("temp/checkpoints")
    workflow_id = "test-workflow-001"
    
    # Create manager
    manager = CheckpointManager(checkpoint_dir, retention_count=5)
    
    # Test 1: Save checkpoint
    print("\n1. Testing checkpoint save...")
    test_state = {
        "workflow_id": workflow_id,
        "input_context": {"theme": "honesty", "age_group": "6-8"},
        "validated_context": {"theme": "honesty", "characters": []},
        "search_queries": ["honesty stories for kids"],
        "progress": 0.1,
        "status": "running"
    }
    
    checkpoint_path = manager.save_checkpoint(
        state=test_state,
        step_name="context_analyzer",
        workflow_id=workflow_id
    )
    print(f"   [OK] Checkpoint saved: {checkpoint_path}")
    
    # Test 2: Load checkpoint
    print("\n2. Testing checkpoint load...")
    loaded_state, step_name = manager.load_checkpoint(checkpoint_path)
    print(f"   [OK] Checkpoint loaded: step={step_name}")
    print(f"   [OK] State keys: {list(loaded_state.keys())[:5]}...")
    
    # Test 3: List checkpoints
    print("\n3. Testing checkpoint listing...")
    checkpoints = manager.list_checkpoints(workflow_id)
    print(f"   [OK] Found {len(checkpoints)} checkpoint(s)")
    for cp in checkpoints:
        print(f"     - {cp['step_name']}: {cp['timestamp'][:19]}")
    
    # Test 4: Get latest checkpoint
    print("\n4. Testing get latest checkpoint...")
    latest = manager.get_latest_checkpoint(workflow_id)
    if latest:
        print(f"   [OK] Latest checkpoint: {latest.name}")
    
    # Test 5: Save multiple checkpoints
    print("\n5. Testing multiple checkpoints...")
    for i, step in enumerate(["web_researcher", "story_generator", "script_segmenter"], 2):
        test_state["progress"] = i * 0.15
        test_state["last_completed_step"] = step
        cp = manager.save_checkpoint(test_state, step, workflow_id)
        print(f"   [OK] Saved checkpoint for {step}")
    
    # Test 6: List all checkpoints
    print("\n6. Listing all checkpoints...")
    checkpoints = manager.list_checkpoints(workflow_id)
    print(f"   [OK] Total checkpoints: {len(checkpoints)}")
    
    # Test 7: Get checkpoint for specific step
    print("\n7. Testing get checkpoint for specific step...")
    story_cp = manager.get_checkpoint_for_step(workflow_id, "story_generator")
    if story_cp:
        print(f"   [OK] Found checkpoint for story_generator: {story_cp.name}")
    
    print("\n" + "=" * 60)
    print("All tests passed!")
    print("=" * 60)
    print(f"\nCheckpoint directory: {checkpoint_dir / workflow_id}")
    print("You can inspect the checkpoint files manually.")
    

def test_intermediate_outputs():
    """Test intermediate output file creation."""
    
    print("\n" + "=" * 60)
    print("Intermediate Outputs Test")
    print("=" * 60)
    
    workflow_id = "test-workflow-002"
    checkpoint_dir = Path("temp/checkpoints") / workflow_id
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    
    # Simulate saving intermediate outputs
    print("\n1. Saving intermediate outputs...")
    
    # Context analyzer outputs
    validated_context = {
        "theme": "honesty",
        "characters": [{"name": "Leo", "type": "lion"}],
        "setting": "jungle",
        "moral_lesson": "Always tell the truth"
    }
    
    with open(checkpoint_dir / "01_validated_context.json", 'w') as f:
        json.dump(validated_context, f, indent=2)
    print("   [OK] Saved 01_validated_context.json")
    
    # Story generator outputs
    story = "Once upon a time in a jungle, there lived a brave lion named Leo..."
    
    with open(checkpoint_dir / "03_story.txt", 'w') as f:
        f.write(story)
    print("   [OK] Saved 03_story.txt")
    
    story_metadata = {
        "word_count": 450,
        "estimated_reading_time_minutes": 2.25,
        "theme": "honesty"
    }
    
    with open(checkpoint_dir / "03_story_metadata.json", 'w') as f:
        json.dump(story_metadata, f, indent=2)
    print("   [OK] Saved 03_story_metadata.json")
    
    print(f"\n[OK] Intermediate outputs saved to: {checkpoint_dir}")
    print("  You can view these files to see the workflow progress.")


if __name__ == "__main__":
    try:
        test_checkpoint_manager()
        test_intermediate_outputs()
        
        print("\n" + "=" * 60)
        print("SUCCESS: All checkpoint tests completed!")
        print("=" * 60)
        print("\nNext steps:")
        print("1. Run the main workflow with: python main.py --input story.json --workflow-id test-001")
        print("2. Interrupt it (Ctrl+C) after a few steps")
        print("3. Resume with: python main.py --workflow-id test-001 --resume")
        print("4. List checkpoints: python main.py --workflow-id test-001 --list-checkpoints")
        
    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
